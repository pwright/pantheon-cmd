#!/usr/bin/python3

import os
import sys
import glob
import yaml
from pcchecks import Regex, icons_check, toc_check
from pcvalidator import Report


class Printing():
    """Create and print report."""

    def __init__(self):
        self.report = {}
        self.count = 0

    def create_report(self, message, items):
        """Generate report."""
        self.count += 1
        if not message in self.report:
            self.report[message] = []
        self.report[message].append(items)

    def print_report(self):
        """Print report."""
        separator = "\n\t"

        for message, items in self.report.items():
            print("\nFAIL: the following {}:".format(message))
            for item in items:
                print('\t' + separator.join(item))


def get_yaml_syntax_errors(self):
    """Check size and syntax of the yaml file"""
    if os.path.getsize(self.yaml_file_location) > 0:

        with open(self.yaml_file_location, 'r') as f:

            try:
                yaml.safe_load(f)
            except yaml.YAMLError:
                print("There's a syntax error in your pantheon2.yml file. Please fix it and try again.\nTo detect an error try running yaml lint on your pantheo2.yml file.")
                sys.exit(2)

    else:
        print("Your pantheon2.yml file is empty; exiting...")
        sys.exit(2)


def get_missing_or_empty_yaml_keys(self):
    """Get yaml keys that are empty or missing."""

    empty_keys = []
    key_missing = []

    with open(self.yaml_file_location, 'r') as f:
        data = yaml.safe_load(f)
        keys = data.keys()

        # check if all required keys exist in the yml file
        required_keys = (['server', 'repository', 'variants', 'assemblies', 'modules', 'resources'])

        for key in required_keys:
            if key not in keys:
                key_missing.append(key)
            else:
                if data[key] is None:
                    empty_keys.append(key)

    return key_missing, empty_keys


def get_missing_keys(self):
    """Return missing keys."""
    key_missing, empty_keys = get_missing_or_empty_yaml_keys(self)

    return(sorted(key_missing, key=str.lower))


def get_empty_values(self):
    """Return empty keys."""
    key_missing, empty_keys = get_missing_or_empty_yaml_keys(self)

    return(sorted(empty_keys, key=str.lower))


def get_missing_variant_keys(report, yaml_file, required_values):
    """Get missing variant keys and check their values"""
    missing_value = []

    #FIXME: this code is redundant as skript exits if get_missing_variant_keys function has any value
    if yaml_file['variants'] is None:
        report.create_report('values are missing under "variants"', sorted(required_values, key=str.lower))
        return

    for item in required_values:
        for variant_values in yaml_file['variants']:
            if item not in variant_values.keys():
                missing_value.append(item)

    if missing_value:
        report.create_report('keys are missing under "variants"', sorted(missing_value, key=str.lower))
        return

    varriant_values_none = []
    cannonical_is_not_true = []
    path_does_not_exist = []
    path_exists = []
    missing_value = []

    for variant_values in yaml_file['variants']:
        for item in required_values:
            if variant_values[item] == None:
                varriant_values_none.append(item)
        if varriant_values_none:
            report.create_report('keys are empty', sorted(varriant_values_none, key=str.lower))

        if variant_values['canonical'] != None:
            if variant_values['canonical'] != True:
                cannonical_is_not_true.append('cannonical')
        if cannonical_is_not_true:
            report.create_report('key is not set to True', sorted(cannonical_is_not_true, key=str.lower))

        if variant_values['path'] != None:
            if not os.path.exists(variant_values['path']):
                path_does_not_exist.append(variant_values['path'])
            else:
                path_exists.append(variant_values['path'])
        if path_does_not_exist:
            report.create_report('files or directories do not exist in your repository', path_does_not_exist)

        if path_exists:
            return path_exists


    false_dir = []
    empty_dir = []

    if yaml_file['resources'] != None:
        for item in (yaml_file['resources']):
            path_to_images_dir = os.path.split(item)[0]
            if not glob.glob(path_to_images_dir):
                false_dir.append(path_to_images_dir)
            else:
                if len(os.listdir(path_to_images_dir)) == 0:
                    empty_dir.append(path_to_images_dir)

    if false_dir:
        report.create_report('files or directories do not exist in your repository', sorted(false_dir, key=str.lower))

    if empty_dir:
        report.create_report('directory is empty', sorted(empty_dir, key=str.lower))


def get_attribute_file_path(report, yaml_file, required_values):
    """Record the attribiutes file."""
    path_exists = get_missing_variant_keys(report, yaml_file, required_values)

    return path_exists


def yaml_validator(self):
    """Validates variant yaml keys and checks the attributes file."""
    prints = Printing()
    report = Report()

    with open(self.yaml_file_location, 'r') as f:
        data = yaml.safe_load(f)

        required_variant_keys = (['name', 'path', 'canonical'])

        get_missing_variant_keys(report, data, required_variant_keys)

        attribute_file = get_attribute_file_path(report, data, required_variant_keys)

        for path in attribute_file:
            with open(path, 'r') as file:
                original = file.read()
                stripped = Regex.MULTI_LINE_COMMENT.sub('', original)
                stripped = Regex.SINGLE_LINE_COMMENT.sub('', stripped)
                stripped = Regex.CODE_BLOCK_DASHES.sub('', stripped)
                stripped = Regex.CODE_BLOCK_DOTS.sub('', stripped)
                stripped = Regex.INTERNAL_IFDEF.sub('', stripped)

                icons_check(report, stripped, path)
                toc_check(report, stripped, path)

    return prints, report


def get_yaml_validation_results(self):
    """Get report for yaml validation."""
    prints, report = yaml_validator(self)

    return prints


def get_attribute_file_validation_results(self):
    """Get report for attributes file validation."""
    prints, report = yaml_validator(self)

    return report
