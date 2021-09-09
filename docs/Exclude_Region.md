# Exclude Obects

The `[exclude_region]` module allows Klipper to exclude regions or
objects while a print is in progress.

The region or object to be excluded is defined by gcode commands included in the file.
The commands need to be inserted in a pre-processing step as the are Klipper specific
and are indepenent of any markers included by slicers.

### Extended GCode Commands for File Markup
These commands are used in the gcode file to be printed, and are inserted by a pre-processing step.

`START_CURRENT_OBJECT`: This command takes a `NAME` parameter and denotes the start of
the gcode for an object on the current layer.  The name should be unique between all
objects in the file being printed, but should be consistent across all layers.

`END_CURRENT_OBJECT`:  Denotes the end of the object's gcode for the layer.  Is paired with
`START_CURRENT_OBJECT`.

`DEFINE_OBJECT`:  Provides a summary of an object in the file.  Typically will be
inserted at the beginning of a file.  This command takes a `NAME` parameter.

### Extended GCode Commands
`EXCLUDE_OBJECT`: This command takes a `NAME` parameter and instructs Klipper to ignore
gcode for that object.

`REMOVE_ALL_EXCLUDED`: Clears the current list of excluded areas and objects.

`LIST_OBJECTS`: Lists the objects known to Klipper.

`LIST_EXCLUDED_OBJECTS`: Lists the excluded objects.