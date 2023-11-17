| **Caso de uso**      | **Solicitar ejecución de archivo** |
| :---        | :---        |
| **Identificador**      | UC08 |
| **Actores**      | Usuario |
| **Precondición**   | Hay al menos un archivo almacenado. |
| **Resultado**   | El usuario puede solicitar la ejecución de un archivo en el listado de archivos disponibles. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario pueda solicitar la ejecución de uno de los archivos disponibles.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En la vista de "Archivos", selecciona el archivo deseado. |  |
| 2      | Cliquea "solicitar ejecución". |  |
| 3      |  | Despliega una ventana de registro de solicitud. |
| 4      | Completa con un comentario y acepta. |  |
| 5      |  | Actualiza la DB y muestra una notificación de éxito. |

**Curso alternativo (eliminar archivo después de usar):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 4a      | Tilda la opción "eliminar después de ejecutar". |  |
