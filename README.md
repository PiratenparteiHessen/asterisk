# Asterisk Administrationsinterface
Eigenes Administrationsinterface für Asterisk 1.x der Piratenpartei Hessen.

## Ursprung
Das Original wurde im Jahre 2010 von [Lothar Krauß](https://wiki.piratenpartei.de/Benutzer:Lothar) für Version 1.4 unter Debian 5 (Lenny) geschrieben.

## Migration
Im Zuge einer Migration des Dienstes Anfang 2017 wurde das Administrationsinterface auf Version 1.8 und Debian 7 (Wheezy) angepasst und zudem mittels [Bootstrap 3](https://getbootstrap.com/) fit für HTML5 und mobile durch die IT der Piratenpartei Hessen gemacht.

## Wiki
Weitere Details finden sich im [Wiki](https://wiki.piratenpartei.de/HE:Telefonkonferenz) der Piratenpartei.

## Schreibrechte (sudo)
Damit das meetmeadmin.cgi (www-data) via meetmeadmin unter /var/asterisk/spool Schreibrechte als User asterisk erhält, ist eine Anpassung von /etc/sudoers notwendig:

    Defaults:www-data !requiretty
    www-data ALL=(asterisk) NOPASSWD: /usr/local/bin/meetmeadmin