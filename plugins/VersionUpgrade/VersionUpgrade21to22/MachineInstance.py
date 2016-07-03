# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

import UM.VersionUpgrade #To indicate that a file is of incorrect format.

import configparser #To read config files.
import io #To write config files to strings as if they were files.

##  Creates a new machine instance instance by parsing a serialised machine
#   instance in version 1 of the file format.
#
#   \param serialised The serialised form of a machine instance in version 1.
#   \return A machine instance instance, or None if the file format is
#   incorrect.
def importFrom(serialised):
    try:
        return MachineInstance(serialised)
    except (configparser.Error, UM.VersionUpgrade.FormatException, UM.VersionUpgrade.InvalidVersionException):
        return None

##  A representation of a machine instance used as intermediary form for
#   conversion from one format to the other.
class MachineInstance:
    ##  Reads version 1 of the file format, storing it in memory.
    #
    #   \param serialised A string with the contents of a machine instance file.
    def __init__(self, serialised):
        config = configparser.ConfigParser(interpolation = None)
        config.read_string(serialised) # Read the input string as config file.

        # Checking file correctness.
        if not config.has_section("general"):
            raise UM.VersionUpgrade.FormatException("No \"general\" section.")
        if not config.has_option("general", "version"):
            raise UM.VersionUpgrade.FormatException("No \"version\" in \"general\" section.")
        if not config.has_option("general", "name"):
            raise UM.VersionUpgrade.FormatException("No \"name\" in \"general\" section.")
        if not config.has_option("general", "type"):
            raise UM.VersionUpgrade.FormatException("No \"type\" in \"general\" section.")
        if int(config.get("general", "version")) != 1: # Explicitly hard-code version 1, since if this number changes the programmer MUST change this entire function.
            raise UM.VersionUpgrade.InvalidVersionException("The version of this machine instance is wrong. It must be 1.")

        self._type_name = config.get("general", "type")
        self._variant_name = config.get("general", "variant", fallback = None)
        self._name = config.get("general", "name")
        self._key = config.get("general", "key", fallback = None)
        self._active_profile_name = config.get("general", "active_profile", fallback = None)
        self._active_material_name = config.get("general", "material", fallback = None)

        self._machine_setting_overrides = {}
        for key, value in config["machine_settings"].items():
            self._machine_setting_overrides[key] = value

    ##  Serialises this machine instance as file format version 2.
    #
    #   This is where the actual translation happens in this case.
    #
    #   \return A serialised form of this machine instance, serialised in
    #   version 2 of the file format.
    def export(self):
        config = configparser.ConfigParser(interpolation = None) # Build a config file in the form of version 2.

        config.add_section("general")
        config.set("general", "name", self._name)
        config.set("general", "id", self._name)
        config.set("general", "type", self._type_name)
        config.set("general", "version", "2") # Hard-code version 2, since if this number changes the programmer MUST change this entire function.

        import VersionUpgrade21to22 # Import here to prevent circular dependencies.
        type_name = VersionUpgrade21to22.VersionUpgrade21to22.VersionUpgrade21to22.translatePrinter(self._type_name)
        active_profile = VersionUpgrade21to22.VersionUpgrade21to22.VersionUpgrade21to22.translateProfile(self._active_profile_name)
        active_material = VersionUpgrade21to22.VersionUpgrade21to22.VersionUpgrade21to22.translateProfile(self._active_material_name)
        if type_name == "ultimaker2_plus":
            if self._variant_name == "0.25 mm":
                variant = "ultimaker2_plus_0.25"
            elif self._variant_name == "0.4 mm":
                variant = "ultimaker2_plus_0.4"
            elif self._variant_name == "0.6 mm":
                variant = "ultimaker2_plus_0.6"
            elif self._variant_name == "0.8 mm":
                variant = "ultimaker2_plus_0.8"
            else:
                variant = self._variant_name
        elif type_name == "ultimaker2_extended_plus":
            if self._variant_name == "0.25 mm":
                variant = "ultimaker2_extended_plus_0.25"
            elif self._variant_name == "0.4 mm":
                variant = "ultimaker2_extended_plus_0.4"
            elif self._variant_name == "0.6 mm":
                variant = "ultimaker2_extended_plus_0.6"
            elif self._variant_name == "0.8 mm":
                variant = "ultimaker2_extended_plus_0.8"
            else:
                variant = self._variant_name
        else:
            variant = self._variant_name

        containers = [
            self._name,
            active_profile,
            active_material,
            variant,
            type_name
        ]
        config.set("general", "containers", ",".join(containers))

        config.add_section("metadata")
        config.set("metadata", "type", "machine")

        VersionUpgrade21to22.VersionUpgrade21to22.VersionUpgrade21to22.translateSettings(self._machine_setting_overrides)
        config.add_section("values")
        for key, value in self._machine_setting_overrides.items():
            config.set("values", key, str(value))

        output = io.StringIO()
        config.write(output)
        return output.getvalue()