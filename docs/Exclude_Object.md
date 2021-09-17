# Exclude Obects

The `[exclude_region]` module allows Klipper to exclude regions or
objects while a print is in progress.

The region or object to be excluded is defined by gcode commands included in the file.
The commands need to be inserted in a pre-processing step as the are Klipper specific
and are indepenent of any markers included by slicers.

### Extended GCode Commands for File Markup
These commands are used in the gcode file to be printed, and are inserted by a pre-processing step.

`START_CURRENT_OBJECT`: This command takes a `NAME` parameter and denotes the start of
the gcode for an object on the current layer.

`END_CURRENT_OBJECT`:  Denotes the end of the object's gcode for the layer.  It is paired with
`START_CURRENT_OBJECT`.  A `NAME` parameter is optional.  A warning will be given if
and `END_CURRENT_OBJECT` command is encountered when it wasn't expected or of the given
name does not match the current object.

`DEFINE_OBJECT`:  Provides a summary of an object in the file.  Typically will be
inserted at the beginning of a file.  Objects don't need to be defined in order to be referenced
by other commands.  The primary purpose of this command is to provide information to the UI
without needing to have parsed the entire gcode file.

It takes the following parameters:

- `NAME`: This parameter is required.  It is the identifier used by other commands in this module.
 The name must be unique among all objects in the file being printed, and must be consistent across all layers.
- `CENTER`: An X,Y coordinate for the object.  Typically it will be in the center of the object, but
   that is not a requirement.  While this parameter is technically optional, not including it will
   likely limit the functionality of other components.  Example: `CENTER=150.07362,138.27616`.
- `POLYGON`: An array of X,Y coordinates that provide an outline for the object.  The polygon information
   is primarly for the use of graphical interfces.  This parameter is optional, but like `CENTER`,
   the functionality of other components may be restricted if it is not given.  It is left to the
   software processing the gcode file to determine the complexity of the polygon being provided.  At a
   minimum, it is recommended that this be a bounding box.
   Example: `POLYGON=[[142.7,130.95],[142.7,145.75],[157.5,145.75],[157.5,130.95]]`

### Extended GCode Commands
`EXCLUDE_OBJECT`: This command takes a `NAME` parameter and instructs Klipper to ignore
gcode for that object.

`LIST_OBJECTS`: Lists the objects known to Klipper.

`LIST_EXCLUDED_OBJECTS`: Lists the excluded objects.

`EXCLUDE_OBJECT_RESET`: Clears the current list objects and excluded objects.