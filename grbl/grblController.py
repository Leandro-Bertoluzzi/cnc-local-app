import logging
from grbl.constants import GRBL_ACTIVE_STATE_ALARM, GRBL_ACTIVE_STATE_IDLE, GRBL_QUERY_COMMANDS, GRBL_REALTIME_COMMANDS, GRBL_SETTINGS
from grbl.grblLineParser import GrblLineParser
from grbl.parsers.grblMsgTypes import *
from utils.serial import SerialService
from serial import SerialException

class GrblController:
    state = {
        'status': {
            'activeState': '',
            'mpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'wpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'ov': []
        },
        'parserstate': {
            'modal': {
                'motion': 'G0', # G0, G1, G2, G3, G38.2, G38.3, G38.4, G38.5, G80
                'wcs': 'G54', # G54, G55, G56, G57, G58, G59
                'plane': 'G17', # G17: xy-plane, G18: xz-plane, G19: yz-plane
                'units': 'G21', # G20: Inches, G21: Millimeters
                'distance': 'G90', # G90: Absolute, G91: Relative
                'feedrate': 'G94', # G93: Inverse time mode, G94: Units per minute
                'program': 'M0', # M0, M1, M2, M30
                'spindle': 'M5', # M3: Spindle (cw), M4: Spindle (ccw), M5: Spindle off
                'coolant': 'M9' # M7: Mist coolant, M8: Flood coolant, M9: Coolant off, [M7,M8]: Both on
            },
            'tool': '',
            'feedrate': '',
            'spindle': ''
        }
    }

    settings = {
        'version': '',
        'parameters': {},
        'checkmode': False
    }

    def __init__(self, logger: logging.Logger):
        # Configure serial interface
        self.serial = SerialService()

        # Configure logger
        file_handler = logging.FileHandler('grbl.log', 'a')
        file_handler.setLevel(logging.INFO)
        file_format = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
        file_handler.setFormatter(file_format)
        self.logger = logger
        self.logger.addHandler(file_handler)

    def connect(self, port: str, baudrate: int) -> dict[str, str]:
        """Starts the GRBL device connected to the given port.
        """
        try:
            response = self.serial.startConnection(port, baudrate)
            self.logger.info('Started USB connection at port %s with a baudrate of %s', port, baudrate)
        except SerialException as error:
            self.logger.critical('Failed opening serial port %s with a baudrate of %s', port, baudrate, exc_info=True)
            raise Exception('Failed opening serial port, verify the connection and close any other connection you may have')

        msgType, payload = self.parseResponse(response)

        if msgType != GRBL_MSG_STARTUP:
            self.logger.critical('Failed starting connection with GRBL')
            raise Exception('Failed starting connection with GRBL: ', payload)

        self.settings['version'] = payload['version']
        responsePayload = payload

        # -- Startup alarm message validation --
        # [MSG:'$H'|'$X' to unlock] - Alarm state is active at initialization.
        # This message serves as a reminder note on how to cancel the alarm state.
        # All g-code commands and some ‘$’ are blocked until the alarm state is cancelled via homing $H or unlocking $X.
        # Only appears immediately after the Grbl welcome message when initialized with an alarm.
        response = self.serial.readLine()
        msgType, payload = self.parseResponse(response)

        if (msgType == GRBL_MSG_FEEDBACK) and ('$H' in payload['message']):
            #responsePayload['homing'] = True
            self.logger.warning('Homing cycle required at startup, handling...')
            self.handleHomingCycle()

        return responsePayload

    def disconnect(self):
        """Ends the communication with the GRBL device.
        """
        self.serial.stopConnection()

        # Removes the file handler from the logger
        for h in self.logger.handlers:
            if isinstance(h, logging.FileHandler):
                self.logger.removeHandler(h)

    def parseResponse(self, response: str) -> tuple[str | None, dict[str, str]]:
        """Returns the parsed response from GRBL.
        """
        self.logger.debug('[Received] Message from GRBL: %s', response)
        msgType, payload = GrblLineParser.parse(response)
        self.logger.info('[Parsed] Message type: %s| Payload: %s', msgType, payload)

        return (msgType, payload)

    def streamLine(self, line: str) -> dict[str, str]:
        """Sends a line of G-code to the GRBL device.
        """
        self.logger.debug('[Sent] G-code line: %s', line)
        response = self.serial.streamLine(line)
        msgType, payload = self.parseResponse(response)

        if msgType == GRBL_RESULT_ERROR:
            self.logger.error('Error executing line: %s. Description: %s', payload['message'], payload['description'])
            raise Exception('Error executing line: ' + payload['message'] + '. Description: ' + payload['description'])
        if msgType == GRBL_MSG_ALARM:
            self.logger.critical('Alarm activated executing line: %s. Description: %s', payload['message'], payload['description'])
            raise Exception('Alarm activated: ' + payload['message'] + '. Description: ' + payload['description'])
        return payload

    def sendCommand(self, command: str) -> list[tuple[str | None, dict[str, str]]]:
        """Sends a GRBL command to the GRBL device.
        Returns all responses from the GRBL device until an 'ok' is found.

        Query commands:
        - '$' : Help
        - '$$' : GRBL settings
        - '$I' : Build/Version info
        - '$H' : Homing cycle
        - '$X' : Disable alarm
        - '$G' : G-code Parser State
        - '$#' : GRBL parameters
        - '$C' : G-code check mode enable/disable

        Real-time Commands:
        - '~' : Cycle Start
        - '!' : Feed Hold
        - '?' : Current Status
        - '\x18' (Ctrl-X) : Reset Grbl
        """
        if (command not in GRBL_QUERY_COMMANDS) and (command not in GRBL_REALTIME_COMMANDS):
            self.logger.error('Invalid GRBL command: %s', command)
            raise Exception('Invalid GRBL command: ' + command)

        self.logger.debug('[Sent] GRBL command: %s', command)
        self.serial.sendLine(command)

        # Reads messages from GRBL until it sends an 'ok' response, or MESSAGES_LIMIT is reached
        # All messages previous to 'ok' are retrieved in an array to be processed later
        responses = []
        msgType = ''
        count = 0
        MESSAGES_LIMIT = 200 if command == '$$' else 15

        while msgType != GRBL_RESULT_OK and count < MESSAGES_LIMIT:
            response = self.serial.readLine()
            msgType, payload = self.parseResponse(response)
            responses.append((msgType, payload))
            count = count + 1

        if (count >= MESSAGES_LIMIT):
            self.logger.error('There was an error processing the command: %s', command)
            raise Exception('There was an error processing the command: ' + command)

        return responses

    # ACTIONS

    def handleHomingCycle(self):
        """Runs the GRBL device's homing cycle.
        """
        #self.sendCommand('$H')

        # Technical debt: Temporary solution, disable alarm
        self.disableAlarm()

    def disableAlarm(self) -> str:
        """Disables an alarm.
        """
        responses = self.sendCommand('$X')

        (msgType, payload) = responses[0]
        if msgType == GRBL_RESULT_OK:
            self.logger.warning('There was no alarm to disable')
            return 'There is no alarm to disable'

        for (msgType, payload) in responses:
            if (msgType == GRBL_MSG_FEEDBACK) and ('Caution: Unlocked' in payload['message']):
                self.logger.info('Alarm was successfully disabled')
                return 'Alarm was successfully disabled'

        self.logger.error('There was an error disabling the alarm')
        raise Exception('There was an error disabling the alarm')

    def toggleCheckMode(self) -> bool:
        """Enables/Disables the "check G-code" mode.

        With this mode enabled, the user can stream a G-code program to Grbl, where it will parse it,
        error-check it, and report ok's and errors:'s without powering on anything or moving.
        """
        responses = self.sendCommand('$C')

        for (msgType, payload) in responses:
            if (msgType == GRBL_MSG_FEEDBACK) and ('Enabled' in payload['message'] or 'Disabled' in payload['message']):
                checkmode = ('Enabled' in payload['message'])
                self.settings['checkmode'] = checkmode
                self.logger.info('Checkmode was successfully updated to %s', checkmode)
                return { 'checkmode' : checkmode }

        self.logger.error('There was an error enabling the check mode')
        raise Exception('There was an error enabling the check mode')

    # QUERIES

    def queryStatusReport(self):
        """Queries and updates the GRBL device's current status.
        """
        responses = self.sendCommand('?')

        for (msgType, payload) in responses:
            if (msgType == GRBL_MSG_STATUS):
                self.state['status'].update(payload)
                self.logger.info('Device status was successfully updated to %s', self.state['status'])
                return self.state['status']

        self.logger.error('There was an error retrieving the device status')
        raise Exception('There was an error retrieving the device status')

    def queryGcodeParserState(self):
        """Queries and updates the GRBL device's current parser state.
        """
        responses = self.sendCommand('$G')

        for (msgType, payload) in responses:
            if (msgType == GRBL_MSG_PARSER_STATE):
                self.state['parserstate'].update(payload)
                self.logger.info('Parser state was successfully updated to %s', self.state['parserstate'])
                return self.state['parserstate']

        self.logger.error('There was an error retrieving the parser state')
        raise Exception('There was an error retrieving the parser state')

    def queryGrblHelp(self):
        """Queries the GRBL 'help' message.
        This message contains all valid GRBL commands.
        """
        responses = self.sendCommand('$')

        for (msgType, payload) in responses:
            if (msgType == GRBL_MSG_HELP):
                return payload

        self.logger.error('There was an error executing the help command')
        raise Exception('There was an error executing the help command')

    def queryGrblParameters(self):
        """Queries and updates the GRBL device's current parameter data.
        """
        responses = self.sendCommand('$#')

        for (msgType, payload) in responses:
            if (msgType == GRBL_MSG_PARAMS):
                name = payload['name']
                self.settings['parameters'][name] = payload['value']

        self.logger.info('Device parameters were successfully updated to %s', self.settings['parameters'])
        return self.settings['parameters']

    def queryGrblSettings(self):
        """Queries the list of GRBL settings with their current values.
        """
        responses = self.sendCommand('$$')

        response = {}

        for (msgType, payload) in responses:
            if (msgType == GRBL_MSG_SETTING):
                key = payload['name']
                setting = None
                for element in GRBL_SETTINGS:
                    if element['setting'] == key:
                        setting = element
                        break
                response[key] = {
                    'value' : payload['value'],
                    'message' : setting['message'],
                    'units' : setting['units'],
                    'description' : setting['description'],
                }

        if not response:
            self.logger.error('There was an error retrieving the GRBL settings')
            raise Exception('There was an error retrieving the GRBL settings')

        return response

    def queryBuildInfo(self):
        """Queries some GRBL device's (firmware) build information.

        Example:
        - {'version': '1.1d.20161014', 'comment': '', 'optionCode': 'VL', 'blockBufferSize': '15', 'rxBufferSize': '128'}
        """
        responses = self.sendCommand('$I')

        response = {}

        for (msgType, payload) in responses:
            if (msgType == GRBL_MSG_VERSION):
                response.update(payload)
                response['raw_version'] = response.pop('raw')
            if (msgType == GRBL_MSG_OPTIONS):
                response.update(payload)
                response['raw_option'] = response.pop('raw')

        if not response:
            self.logger.error('There was an error retrieving the build info')
            raise Exception('There was an error retrieving the build info')

        return response

    # GETTERS

    def getMachinePosition(self) -> dict[str, str]:
        """Returns the GRBL device's current machine position.

        Example: { 'x': '0.000', 'y': '0.000', 'z': '0.000' }
        """
        return self.state['status']['mpos']

    def getWorkPosition(self) -> dict[str, str]:
        """Returns the GRBL device's current work position.

        Example: { 'x': '0.000', 'y': '0.000', 'z': '0.000' }
        """
        return self.state['status']['wpos']

    def getModalGroup(self) -> dict[str, str]:
        """Returns the GRBL device's current modal state.

        Example: { 'motion': 'G0', 'wcs': 'G54', 'plane': 'G17', 'units': 'G21', 'distance': 'G90', 'feedrate': 'G94', 'program': 'M0', 'spindle': 'M5', 'coolant': 'M9' }

        Fields description:
            - 'motion': G0, G1, G2, G3, G38.2, G38.3, G38.4, G38.5, G80
            - 'wcs': G54, G55, G56, G57, G58, G59
            - 'plane': G17: xy-plane, G18: xz-plane, G19: yz-plane
            - 'units': G20: Inches, G21: Millimeters
            - 'distance': G90: Absolute, G91: Relative
            - 'feedrate': G93: Inverse time mode, G94: Units per minute
            - 'program': M0, M1, M2, M30
            - 'spindle': M3: Spindle (cw), M4: Spindle (ccw), M5: Spindle off
            - 'coolant': M7: Mist coolant, M8: Flood coolant, M9: Coolant off, [M7,M8]: Both on
        """
        return self.state['parserstate']['modal']

    def getTool(self) -> str:
        """Returns the GRBL device's current tool.
        """
        return self.state['parserstate']['tool']

    def getParameters(self):
        """Returns the GRBL device's current parameter data.

        Example: {
            'G54' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G55' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G56' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G57' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G58' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G59' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G28' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G30' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G92' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'TLO' : 0.000,
            'PRB' : { 'x': '0.000', 'y': '0.000', 'z': '0.000', 'result': True }
        }
        """
        return self.settings['parameters']

    def getCheckModeEnabled(self) -> bool:
        """Returns if the GRBL device is currently configured in check mode.
        """
        return self.settings['checkmode']

    def isAlarm(self) -> bool:
        """Checks if the GRBL device is currently in ALARM state.
        """
        activeState = self.state['status']['activeState']
        return activeState == GRBL_ACTIVE_STATE_ALARM

    def isIdle(self) -> bool:
        """Checks if the GRBL device is currently in IDLE state.
        """
        activeState = self.state['status']['activeState']
        return activeState == GRBL_ACTIVE_STATE_IDLE