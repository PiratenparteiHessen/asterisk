#! /bin/bash

# Dieses Shell-Script stellt ein Webformular zur Administration einer
# Telefonkonferenz in Asterisk zur Verfügung. Der Aufruf des CLI von
# Asterisk erfolgt über ein Wrapper-Programm meetmeadmin, welches mittels
# Set-UID- / Set-GID-Bit den Zugriff auf die Asterisk-Konfiguration
# und den Socket zur Steuerung erhalten muss
# Author: Lothar Krauß (mailto: pirat@lkrauss.de)
# Lizenz: CC-BY


ADMINBIN='sudo -u asterisk /usr/local/bin/meetmeadmin'

p_loginform()
{
  echo '      <div id="loginForm">'
  echo '        <form method="post" action="meetmeadmin.cgi">'
  echo '          <div class="form-group">'
  echo '            <label class="sr-only" for="raum">Raumnummer:</label>'
  echo '            <div class="input-group">'
  echo '              <span class="input-group-addon"><i class="glyphicon glyphicon-phone-alt"></i></span>'
  echo '              <input type="text" class="form-control" id="raum" name="raum" value="'$RAUM'" placeholder="Raumnummer" required="">'
  echo '            </div>'
  echo '          </div>'
  echo '          <div class="form-group">'
  echo '            <label class="sr-only" for="pin">PIN:</label>'
  echo '            <div class="input-group">'
  echo '              <span class="input-group-addon"><i class="glyphicon glyphicon-barcode"></i></span>'
  echo '              <input type="text" class="form-control" id="pin" name="pin" value="'$PIN'" placeholder="PIN" required="">'
  echo '            </div>'
  echo '          </div>'
  echo '          <div class="form-group">'
  echo '            <button type="submit" name="aktion" value="Einloggen" class="btn btn-default">Einloggen</button>'
  echo '          </div>'
  echo '        </form>'
  echo '      </div>'
}

p_buttons()
{
  echo '        <div class="row">'
  echo '          <div class="col-xs-5 form-inline">'
  #echo '            <span>Raum: </span>'
  echo '            <div class="form-group">'
  echo '              <button type="submit" name="aktion" value="Schliessen" class="btn btn-default"><span class="glyphicon glyphicon-folder-close" aria-hidden="true"></span> Schliessen</button>'
  echo '            </div>'
  echo '            <div class="form-group">'
  echo '              <button type="submit" name="aktion" value="Öffnen" class="btn btn-default"><span class="glyphicon glyphicon-folder-open" aria-hidden="true"></span> Öffnen</button>'
  echo '            </div>'
  echo '          </div>'
  echo '          <div class="col-xs-7 form-inline text-right">'
  #echo '            <span>Teilnehmer: </span>'
  echo '            <div class="form-group">'
  echo '              <button type="submit" name="aktion" value="Stumm" class="btn btn-default"><span class="glyphicon glyphicon-volume-off" aria-hidden="true"></span> Stumm</button>'
  echo '            </div>'
  echo '            <div class="form-group">'
  echo '              <button type="submit" name="aktion" value="Sprechen" class="btn btn-default"><span class="glyphicon glyphicon-volume-up" aria-hidden="true"></span> Sprechen</button>'
  echo '            </div>'
  echo '            <div class="form-group">'
  echo '              <button type="submit" name="aktion" value="Ausschliessen" class="btn btn-default"><span class="glyphicon glyphicon-ban-circle" aria-hidden="true"></span> Ausschliessen</button>'
  echo '            </div>'
  echo '          </div>'
  echo '        </div>'
}

p_endhtml()
{
  echo '    </div>'
  echo '    '
  echo '    <!-- jQuery (necessary for Bootstrap'"'"'s JavaScript plugins) -->'
  echo '    <script src="/js/jquery.min.js"></script>'
  echo '    <!-- Include all compiled plugins (below), or include individual files as needed -->'
  echo '    <script src="/js/bootstrap.min.js"></script>'
  echo '  </body>'
  echo '</html>'
}

DATEN=""
RAUM=""
PIN=""
AKTION=""
SAMMEL=""
CLOSE=""
STATUS=""
STREAM=""
RECORD=""

#echo $REQUEST_METHOD

if [ "$REQUEST_METHOD" = "POST" ]
then
  DATEN=`/bin/cat | /bin/sed -e 's,[^0-9a-zA-Z&=],,g' -e 's,&, ,g'`
  #echo $DATEN

  for x in $DATEN
  do
    feld=${x%=*}
    #echo $feld
    #echo "\n"

    wert=${x#*=}
    #echo $wert
    #echo "\n"

    case $feld in
      raum)
        RAUM="$wert"
        ;;
      pin)
        PIN="$wert"
        ;;
      close)
        CLOSE="$wert"
        ;;
      aktion)
        AKTION="$wert"
        ;;
      mark)
        SAMMEL="$SAMMEL $wert"
        ;;
    esac
  done
fi


if [ "$AKTION" = "Download" -a -r /var/spool/asterisk/monitor/raum$RAUM.gsm ]
then
  $ADMINBIN test $RAUM $PIN
  if [ "$?" = "0" ]
  then
    echo "Content-type: application/octed-stream"
    echo "Content-disposition: filename=raum$RAUM.ogg"
    echo ""
    sox /var/spool/asterisk/monitor/raum$RAUM.gsm -t ogg -
    exit 0
  fi
fi

/bin/cat <<ende1
Content-type: text/html

<!DOCTYPE html>
<html lang="de">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->

    <title>Piratenpartei Hessen - Administration Telefonkonferenz</title>

    <!-- Bootstrap -->
    <link href="/css/bootstrap.min.css" rel="stylesheet">
    <!-- App -->
    <link href="/css/style.css" rel="stylesheet">
  </head>

  <body>
    <div class="container">
      <img src="/img/pph_telefonkonferenz.png" width="266" height="90" alt="Telefonkonferenz Hessen" />
  
ende1

#echo $AKTION

if [ "$AKTION" = "Ausloggen" ]
then
  RAUM=""
  PIN=""
fi

if [ "$RAUM" = "" -o "$PIN" = "" ]
then
  p_loginform
  p_endhtml
  exit 0
fi

if [ "$AKTION" = "Einloggen" ]
then
  #einloggen=`$ADMINBIN`
  einloggen=`$ADMINBIN test $RAUM $PIN`
  #echo $einloggen
  #echo "\n"
  #echo $?
  #echo "\n"
  if [ "$?" != "0" ]
  then
    sleep 5
    p_loginform
    echo '      <div class="alert alert-danger" role="alert">Fehler beim Einloggen</div>'
    p_endhtml
    exit 0
  fi
fi

if [ "$AKTION" = "C396ffnen" ]
then
  $ADMINBIN unlock $RAUM $PIN
  if [ "$?" != "0" ]
  then
    p_loginform
    echo '      <div class="alert alert-danger" role="alert">Fehler beim &OUml;effnen</div>'
    p_endhtml
    exit 0
  fi
  CLOSE=0
elif [ "$AKTION" = "Schliessen" ]
then
  $ADMINBIN lock $RAUM $PIN
  if [ "$?" != "0" ]
  then
    p_loginform
    echo '      <div class="alert alert-danger" role="alert">Fehler beim Schiessen</div>'
    p_endhtml
    exit 0
  fi
  CLOSE=1
elif [ "$AKTION" = "Stream" ]
then
  x=`ps f -u asterisk | grep /var/www/asterisk/cgi-bin/ices/raum$RAUM.xml`
  #echo $x
  #echo "\n"
  if [ "$x" != "" ]
  then
    STATUS="Stream l&auml;uft bereits"
  else
    $ADMINBIN stream $RAUM $PIN
    if [ "$?" != "0" ]
    then
      p_loginform
      echo '<div class="alert alert-danger" role="alert">Fehler beim Stream Starten</div>'
      p_endhtml
      exit 0
    fi
    sleep 3
  fi
elif [ "$AKTION" = "Record" ]
then
  x=`$ADMINBIN list $RAUM $PIN|grep '!0!Record!Local/81'`
  if [ "$x" != "" ]
  then
    STATUS="Aufzeichnung l&auml;uft bereits"
  else
    $ADMINBIN record $RAUM $PIN
    if [ "$?" != "0" ]
    then
      p_loginform
      echo '<div class="alert alert-danger" role="alert">Fehler beim Aufzeichnung Starten</div>'
      p_endhtml
      exit 0
    fi
    sleep 3
  fi
elif [ "$AKTION" = "Delete" ]
then
  $ADMINBIN delrecord $RAUM $PIN
  if [ "$?" != "0" ]
  then
      p_loginform
      echo '<div class="alert alert-danger" role="alert">Fehler beim L&ouml;schen der Aufzeichnung</div>'
      p_endhtml
      exit 0
  fi
elif [ "$AKTION" = "Stumm" ]
then
  if [ "$SAMMEL" = "" ]
  then
     STATUS="Bitte mindestens einen Teilnehmer markieren"
  else
     $ADMINBIN mute $RAUM $PIN $SAMMEL
     if [ "$?" != "0" ]
     then
       p_loginform
       echo '<div class="alert alert-danger" role="alert">Fehler beim Stummschalten</div>'
       p_endhtml
       exit 0
     fi
  fi
elif [ "$AKTION" = "Sprechen" ]
then
  if [ "$SAMMEL" = "" ]
  then
     STATUS="Bitte mindestens einen Teilnehmer markieren"
  else
     $ADMINBIN unmute $RAUM $PIN $SAMMEL
     if [ "$?" != "0" ]
     then
       p_loginform
       echo '<div class="alert alert-danger" role="alert">Fehler beim Freischalten</div>'
       p_endhtml
       exit 0
     fi
  fi
elif [ "$AKTION" = "Ausschliessen" ]
then
  if [ "$SAMMEL" = "" ]
  then
     STATUS="Bitte mindestens einen Teilnehmer markieren"
  else
     $ADMINBIN kick $RAUM $PIN $SAMMEL
     if [ "$?" != "0" ]
     then
       p_loginform
       echo '<div class="alert alert-danger" role="alert">Fehler beim Ausschliessen</div>'
       p_endhtml
       exit 0
     fi
     sleep 3
  fi
fi

if [ "$STATUS" = "" ]
then
  if [ "$CLOSE" = "0" ]
  then
     STATUS="Raum ist ge&ouml;ffnet"
  elif [ "$CLOSE" = "1" ]
  then
     STATUS="Raum ist geschlossen"
  else
     STATUS="&nbsp;"
  fi
fi

#
# FORM START
#
echo '      <form method="post" action="meetmeadmin.cgi">'
echo '        <input type="hidden" name="raum" value='"$RAUM"'>'
echo '        <input type="hidden" name="pin" value='"$PIN"'>'
echo '        <input type="hidden" name="close" value='"$CLOSE"'>'


#
# RAUMINFO
#
echo '        <div class="row">'
echo '          <div class="col-xs-8 form-inline">'
echo '            <div class="form-group" style="width: 200px">'
echo '              <div class="input-group">'
echo '                <div class="input-group-addon">Raumnummer:</div>'
echo '                  <input type="text" class="form-control" id="raumnummer" value="'$RAUM'" readonly >'
echo '                </div>'
echo '              </div>'
echo '              <div class="form-group">'
echo '                <button type="submit" name="aktion" value="Ausloggen" class="btn btn-default"><span class="glyphicon glyphicon-off" aria-hidden="true"></span> Ausloggen</button>'
echo '              </div>'
echo '            </div>'
echo '          <div class="col-xs-4 text-right"><button type="submit" name="aktion" value="Aktualisieren" class="btn btn-default"><span class="glyphicon glyphicon-refresh" aria-hidden="true"></span> Aktualisieren</button></div>'
echo '        </div>'


#
# STATUS
#
echo '        <div class="panel panel-default">'
echo '          <div class="panel-heading">Status</div>'
echo '            <div class="panel-body">'$STATUS'</div>'
echo '        </div>'


#
# DETECT STREAMING
#
x=`ps f -u asterisk | grep /var/www/asterisk/cgi-bin/ices/raum$RAUM.xml`
#echo "x: "$x"<br />\\n"
if [ "$x" = "" ]
then
  STREAM=0
else
  STREAM=1
fi
#echo $STREAM"<br />\\n";

echo '        <div class="row">'
echo '          <div class="col-xs-12 form-inline">'
if [ "$STREAM" = "0" ]
then
  echo '          <div class="form-group">'
  echo '            <button type="submit" name="aktion" value="Stream" class="btn btn-default"><span class="glyphicon glyphicon-bullhorn" aria-hidden="true"></span> Stream</button>'
  echo '          </div>'
else
  echo '          <span class="label label-info lb-md"><span class="glyphicon glyphicon-bullhorn" aria-hidden="true"></span> Stream</span>'
  echo '          <a href="http://sip2.piratenpartei-hessen.de:8080/raum'$RAUM'.ogg" target="_blank">http://sip2.piratenpartei-hessen.de:8080/raum'$RAUM'.ogg</a>'
fi
echo '          </div>'
echo '        </div>'


#
# DETECT RECORDING
#
x=`$ADMINBIN list $RAUM $PIN|grep '!0!Record!Local/81'`
#echo "x: "$x"<br />\\n"
if [ "$x" == "" ]
then
  if [ -r /var/spool/asterisk/monitor/raum$RAUM.gsm ]
  then
    RECORD=9
  else
    RECORD=0
  fi
else
  if [ -r /var/spool/asterisk/monitor/raum$RAUM.gsm ]
  then
    RECORD=9
  else
    RECORD=1
  fi
fi
#echo $RECORD"<br />\\n";

echo '        <div class="row">'
echo '          <div class="col-xs-12 form-inline">'
if [ "$RECORD" = "0" ]
then
  echo '          <div class="form-group">'
  echo '            <button type="submit" name="aktion" value="Record" class="btn btn-default"><span class="glyphicon glyphicon-hdd" aria-hidden="true"></span> Record</button>'
  echo '          </div>'
elif  [ "$RECORD" = "1" ]
then
  echo '          <span class="label label-danger lb-md"><span class="glyphicon glyphicon-hdd" aria-hidden="true"></span> Record</span>'
  echo '          <span>Aufnahme gelöscht</span>'
elif  [ "$RECORD" = "9" ]
then
  echo '          <span class="label label-info lb-md"><span class="glyphicon glyphicon-hdd" aria-hidden="true"></span> Record</span>'
  echo '          <div class="form-group">'
  echo '            <button type="submit" name="aktion" value="Download" class="btn btn-default"><span class="glyphicon glyphicon-download-alt" aria-hidden="true"></span> Download</button>'
  echo '          </div>'
  echo '          <div class="form-group">'
  echo '            <button type="submit" name="aktion" value="Delete" class="btn btn-default"><span class="glyphicon glyphicon-trash" aria-hidden="true"></span> Delete</button>'
  echo '          </div>'
fi
echo '          </div>'
echo '        </div>'


p_buttons


#
# TEILNEHMER
#
echo '        <div class="row">'
echo '          <div class="col-xs-12">'
echo '            <table class="table table-hover table-condensed">'
echo '              <thead>'
echo '                <tr>'
echo '                  <td>#</td>'
echo '                  <td>Nummer</td>'
echo '                  <td>Name</td>'
echo '                  <td>Kanal</td>'
echo '                  <td>Dauer</td>'
echo '                  <td>Status</td>'
echo '                  <td><input type="checkbox" name="mark" value="all"></td>'
echo '                </tr>'
echo '              </thead>'

echo '              <tr>'
$ADMINBIN list $RAUM $PIN|/usr/bin/awk -F '!' '{
   if ($7 == "1")
   {
     printf("<tr class=\"active\">");
   }
   else
   {
     printf("<tr>");
   }
   printf("<td>%s</td>",$1);            # idx
   printf("<td>%s</td>",$2);            # nummer
   printf("<td>%s</td>",$3);            # name
   printf("<td>%s</td>",$4);            # kanal
   printf("<td>%s</td>",$10);           # dauer
   if      ($7 == "1")  { printf("<td class=\"warning\">stumm</td>"); }
   else if ($8 == "1")  { printf("<td class=\"info\">spricht</td>"); }
   else if ($8 == "-1") { printf("<td>unbekannt</td>"); }
   else                 { printf("<td class=\"success\">bereit</td>"); }
   printf("<td><input type=\"checkbox\" name=\"mark\" value=\"%s\"></td>",$1);
   printf("</tr>\n");
}'
echo '</table>'


p_buttons


echo '      </form>'


p_endhtml


exit 0
