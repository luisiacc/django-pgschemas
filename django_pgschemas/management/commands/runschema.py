import argparse

from django.core.management import call_command, get_commands, load_command_class
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from . import WrappedSchemaOption


class Command(WrappedSchemaOption, BaseCommand):
    help = "Wrapper around django commands for use with an individual schema"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("command_name", help="The command name you want to run")

    def command_from_arg(self, arg):
        *chunks, command = arg.split(".")
        path = ".".join(chunks)
        if not path:
            path = get_commands().get(command)
            if not path:
                raise CommandError("Unknown command: %s" % arg)
            return load_command_class(path, command)
        try:
            return load_command_class(path, command)
        except Exception:
            raise CommandError("Unknown command: %s" % arg)

    def run_from_argv(self, argv):
        """
        Changes the option_list to use the options from the wrapped command.
        Adds schema parameter to specify which schema will be used when
        executing the wrapped command.
        """
        # load the command object.
        if len(argv) <= 2:
            return
        target_class = self.command_from_arg(argv[2])
        # Ugly, but works. Delete command_name from the argv, parse the schema manually
        # and forward the rest of the arguments to the actual command being wrapped.
        del argv[1]
        schema_parser = argparse.ArgumentParser()
        super().add_arguments(schema_parser)
        schema_ns, args = schema_parser.parse_known_args(argv)
        current_schema = getattr(connection, "schema_name", "public")
        for schema in self.get_schemas_from_options(schema=schema_ns.schema):
            self.print_switch_schema(schema)
            connection.set_schema(schema)
            target_class.run_from_argv(args)
        connection.set_schema(current_schema)

    def handle(self, *args, **options):
        target = self.command_from_arg(options.pop("command_name"))
        schemas = self.get_schemas_from_options(**options)
        options.pop("schema")
        options.pop("skip_schema_creation")
        current_schema = getattr(connection, "schema_name", "public")
        for schema in schemas:
            self.print_switch_schema(schema)
            connection.set_schema(schema)
            call_command(target, *args, **options)
        connection.set_schema(current_schema)
