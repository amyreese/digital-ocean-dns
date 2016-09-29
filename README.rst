digital-ocean-dns
=================

Generate and sync DNS zones from YAML to Digital Ocean's domains API.


setup
-----

This requires a few Python modules to run.  Install using ``pip``::

    $ pip install -r requirements.txt

Build a zone config in YAML format with the following format, or start from
the `sample config`_ included in this repo::

    token: your-digital-ocean-api-token
    address: 127.0.0.1
    defaults:
        - "NS @ ns1.digitalocean.com"
    ---
    domain.com:
        - "A @ {address}"


usage
-----

Check the current state of your domain records in Digital Ocean::

    $ ./dodns.py print domains.yml
    noswap.com
         NS @          ns1.digitalocean.com
         NS @          ns2.digitalocean.com
         NS @          ns3.digitalocean.com
          A @          127.0.0.1

Generate the expected state of your domains with the given configuration::

    $ ./dodns.py calc domains.yml
    noswap.com
         NS @          ns1.digitalocean.com.
         NS @          ns2.digitalocean.com.
         NS @          ns3.digitalocean.com.
         MX          1 aspmx.l.google.com.
         MX          5 alt1.aspmx.l.google.com.
         MX          5 alt2.aspmx.l.google.com.
         MX         10 alt3.aspmx.l.google.com.
         MX         10 alt4.aspmx.l.google.com.
        TXT @          keybase-site-verification=61SfD6EF6d3aurMV1ZehczN0OBgpPkjGlac3psdFw5s
        TXT @          v=spf1 include:_spf.google.com a mx -all
      CNAME *          @
       AAAA @          ::1
          A @          127.0.0.1

Calculate the differences between Digital Ocean and your configuration::

    $ ./dodns.py diff domains.yml
    noswap.com
    +    MX          1 aspmx.l.google.com.
    +    MX          5 alt1.aspmx.l.google.com.
    +    MX          5 alt2.aspmx.l.google.com.
    +    MX         10 alt3.aspmx.l.google.com.
    +    MX         10 alt4.aspmx.l.google.com.
    +   TXT @          keybase-site-verification=61SfD6EF6d3aurMV1ZehczN0OBgpPkjGlac3psdFw5s
    +   TXT @          v=spf1 include:_spf.google.com a mx -all
    + CNAME *          @
    +  AAAA @          ::1

Sync differences from configuration back to Digital Ocean::

    $ ./dodns.py sync domains.yml

Verify new state in Digital Ocean::

    $ ./dodns.py print domains.yml
    noswap.com
         NS @          ns1.digitalocean.com
         NS @          ns2.digitalocean.com
         NS @          ns3.digitalocean.com
         MX          1 aspmx.l.google.com
         MX          5 alt1.aspmx.l.google.com
         MX          5 alt2.aspmx.l.google.com
         MX         10 alt3.aspmx.l.google.com
         MX         10 alt4.aspmx.l.google.com
        TXT @          keybase-site-verification=61SfD6EF6d3aurMV1ZehczN0OBgpPkjGlac3psdFw5s
        TXT @          v=spf1 include:_spf.google.com a mx -all
      CNAME *          noswap.com.
       AAAA @          ::1
          A @          127.0.0.1


license
-------

Copyright 2016 John Reese, and licensed under the MIT License.
See the ``LICENSE`` file for details.


.. _sample config: https://github.com/jreese/digital-ocean-dns/blob/master/domains.yml
