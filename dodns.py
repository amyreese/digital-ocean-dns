#!/usr/bin/env python2

# Copyright 2016 John Reese
# Licensed under the MIT license

from __future__ import print_function

import click
import functools
import sys
import yaml

from digitalocean import Domain, Record, Error

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

TOKEN = ''
OPTIONS = {}
DOMAINS = {}
DEFAULTS = []

ORDER = ['NS', 'MX', 'TXT', 'CNAME', 'AAAA', 'A']


def parse_record(row, domain):
    row = row.format(domain=domain.name, **OPTIONS)
    row = row.split(' ', 2)

    if row[0] == 'MX':
        row = [row[0], row[1]] + row[2].rsplit(' ', 1)
        row[3] = int(row[3])
    else:
        row += [None]

    return Record(
        domain_name=domain.name,
        type=row[0],
        name=row[1],
        data=row[2],
        priority=row[3],
        token=TOKEN,
    )


def records_key(r):
    return (ORDER.index(r.type), r.name, r.priority, r.data)


def generate_records(domain):
    extras = DOMAINS[domain.name]
    if not extras:
        extras = []

    records = [
        parse_record(row, domain) for row in DEFAULTS + extras
    ]

    return sorted(records, key=records_key)


def fetch_records(domain):
    records = domain.get_records()

    for record in records:
        if record.type == 'CNAME' and record.data == '@':
            record.data = '{}.'.format(record.domain)

    return records


def diff_records(ideal, actual):
    add = list(ideal)
    remove = list(actual)

    for need in ideal:
        for have in actual:
            if (need.type == have.type and
                    need.name == have.name and
                    need.data.rstrip('.') == have.data.rstrip('.') and
                    need.priority == have.priority):
                add.remove(need)
                remove.remove(have)

    return add, remove


def print_records(records, prefix=' '):
    for record in records:
        if record.type == 'MX':
            args = (prefix, record.type, record.priority, record.data)
        else:
            args = (prefix, record.type, record.name, record.data)

        print('{} {:>5} {:10} {}'.format(*args))


def load_domains():
    domains = []

    for name in sorted(DOMAINS):
        domain = Domain(token=TOKEN, name=name)

        try:
            domain.load()
        except Error:
            domain.ip_address = '127.0.0.1'
            domain.create()

        domains.append(domain)

    return domains


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('--token', default=None, help='Digital Ocean API token')
def cli(token, infile='-'):
    '''
    Sync DNS zones to Digital Ocean domains.
    '''

    global TOKEN

    TOKEN = token


def domain_command(name=None):
    def wrapper(fn):
        @cli.command(name)
        @click.argument(
            'infile', default='-',
            type=click.Path(exists=True, dir_okay=False, allow_dash=True),
        )
        @functools.wraps(fn)
        def wrapped(infile, *args, **kwargs):
            global TOKEN, OPTIONS, DEFAULTS, DOMAINS

            if infile == '-':
                data = sys.stdin.read()
            else:
                with open(infile) as fh:
                    data = fh.read()

            OPTIONS, DOMAINS = yaml.safe_load_all(data)
            TOKEN = TOKEN or OPTIONS.get('token', '')
            DEFAULTS = OPTIONS.get('defaults', [])

            if not TOKEN:
                print('Error: no API token specified')
                sys.exit(1)

            for domain in load_domains():
                fn(domain, *args, **kwargs)

        return wrapped
    return wrapper


@domain_command()
def gen(domain):
    '''
    Generate the expected domain state
    '''
    records = generate_records(domain)

    print(domain.name)
    print_records(records)


@domain_command('print')
def print_cmd(domain):
    '''
    Print the current domain state
    '''
    print(domain.name)
    print_records(fetch_records(domain))


@domain_command()
def diff(domain):
    '''
    Calculate differences from config
    '''
    ideal = generate_records(domain)
    actual = fetch_records(domain)

    add, remove = diff_records(ideal, actual)

    if add or remove:
        print(domain.name)
        print_records(remove, prefix='-')
        print_records(add, prefix='+')


@domain_command()
def clear(domain):
    '''
    Remove all records for all domains
    '''
    for record in domain.get_records():
        record.destroy()


@domain_command()
def sync(domain):
    '''
    Sync domain config to production
    '''
    ideal = generate_records(domain)
    actual = fetch_records(domain)

    add, remove = diff_records(ideal, actual)

    for record in remove:
        record.destroy()

    for record in add:
        record.create()


if __name__ == '__main__':
    cli()
