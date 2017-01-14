#! /bin/bash

# Dieses Shell-Script stellt ein Webformular zur Administration einer
# Telefonkonferenz in Asterisk zur Verfügung. Der Aufruf des CLI von
# Asterisk erfolgt über ein Wrapper-Programm meetmeadmin, welches mittels
# Set-UID- / Set-GID-Bit den Zugriff auf die Asterisk-Konfiguration
# und den Socket zur Steuerung erhalten muss
# Author: Lothar Krauß (mailto: pirat@lkrauss.de)
# Lizenz: CC-BY


ADMINBIN=/opt/asterisk/sbin/meetmeadmin

p_loginform()
{
  echo '<FORM Method="POST" Action="meetmeadmin.cgi">'
  echo 'Raumnummer: <INPUT Type="TEXT" Name="raum" size=4 Value="'$RAUM'">'
  echo 'PIN: <INPUT Type="PASSWORD" Name="pin" size=8 Value="'$PIN'">'
  echo '<INPUT Type="SUBMIT" Name="aktion" Value="Einloggen">'
  echo '</FORM>'
}

p_buttons()
{
  echo '<TR><TD>'
  echo '<INPUT Type="SUBMIT" Name="aktion" Value="Schliessen">'
  echo '<INPUT Type="SUBMIT" Name="aktion" Value="Öffnen">'
  echo '</TD><TD align="right">Teilnehmer:'
  echo '<INPUT Type="SUBMIT" Name="aktion" Value="Stumm">'
  echo '<INPUT Type="SUBMIT" Name="aktion" Value="Sprechen">'
  echo '<INPUT Type="SUBMIT" Name="aktion" Value="Ausschliessen">'
  echo '</TD></TR>'
}

p_endhtml()
{
  echo '</body>'
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

if [ "$REQUEST_METHOD" = "POST" ]
then
  DATEN=`/bin/cat | /bin/sed -e 's,[^0-9a-zA-Z&=],,g' -e 's,&, ,g'`
  for x in $DATEN
  do
    feld=${x%=*}
    wert=${x#*=}
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

if [ "$AKTION" = "Download" -a -r /opt/asterisk/var/spool/asterisk/monitor/raum$RAUM.gsm ]
then
  $ADMINBIN test $RAUM $PIN
  if [ "$?" = "0" ]
  then
    echo "Content-type: application/octed-stream"
    echo "Content-disposition: filename=raum$RAUM.ogg"
    echo ""
    sox /opt/asterisk/var/spool/asterisk/monitor/raum$RAUM.gsm -t ogg -
    exit 0
  fi
fi

/bin/cat <<ende1
Content-type: text/html

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
  <title>Piratenpartei Hessen - Administration Telefonkonferenz</title>
  <meta http-equiv="content-type" content="text/html; charset=iso-8859-1">
</head>
<body>
ende1

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
  $ADMINBIN test $RAUM $PIN
  if [ "$?" != "0" ]
  then
    sleep 5
    p_loginform
    echo '<h3>Fehler beim Einloggen</h3>'
    p_endhtml
    exit 0
  fi
fi

if [ "$AKTION" = "D6ffnen" ]
then
  $ADMINBIN unlock $RAUM $PIN
  if [ "$?" != "0" ]
  then
    p_loginform
    echo '<h3>Fehler beim &OUml;effnen</h3>'
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
    echo '<h3>Fehler beim Schiessen</h3>'
    p_endhtml
    exit 0
  fi
  CLOSE=1
elif [ "$AKTION" = "Stream" ]
then
  x=`ps -fu asterisk | grep /opt/asterisk/ices/raum$RAUM.xml`
  if [ "$x" != "" ]
  then
    STATUS="Stream l&auml;uft bereits"
  else
    $ADMINBIN stream $RAUM $PIN
    if [ "$?" != "0" ]
    then
      p_loginform
      echo '<h3>Fehler beim Stream Starten</h3>'
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
      echo '<h3>Fehler beim Aufzeichnung Starten</h3>'
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
      echo '<h3>Fehler beim L&ouml;schen der Aufzeichnung</h3>'
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
       echo '<h3>Fehler beim Stummschalten</h3>'
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
       echo '<h3>Fehler beim Freischalten</h3>'
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
       echo '<h3>Fehler beim Ausschliessen</h3>'
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

echo '<FORM Method="POST" Action="meetmeadmin.cgi">'
echo '<INPUT Type="HIDDEN" Name="raum" Value='"$RAUM"'>'
echo '<INPUT Type="HIDDEN" Name="pin" Value='"$PIN"'>'
echo '<INPUT Type="HIDDEN" Name="close" Value='"$CLOSE"'>'
echo '<TABLE><TR>'
echo '<TD>Raumnummer: '$RAUM'&nbsp;&nbsp'
echo '<INPUT Type="SUBMIT" Name="aktion" Value="Ausloggen">'
echo '</TD><TD align="right">'
echo '<INPUT Type="SUBMIT" Name="aktion" Value="Aktualisieren">'
echo '</TD></TR>'

echo '<TR><TD colspan="2">'
echo '<hr><h3>'$STATUS'</h3><hr>'
echo '</TD></TR>'

x=`ps -fu asterisk | grep /opt/asterisk/ices/raum$RAUM.xml`
if [ "$x" = "" ]
then
  STREAM=0
else
  STREAM=1
fi
x=`$ADMINBIN list $RAUM $PIN|grep '!0!Record!Local/81'`
if [ "$x" = "" ]
then
  if [ -r /opt/asterisk/var/spool/asterisk/monitor/raum$RAUM.gsm ]
  then
    RECORD=9
  else
    RECORD=0
  fi
else
  RECORD=1
fi

echo '<TR><TD colspan="2">'
if [ "$STREAM" = "0" ]
then
  echo '<INPUT Type="SUBMIT" Name="aktion" Value="Stream">'
fi
if [ "$RECORD" = "0" ]
then
  echo '<INPUT Type="SUBMIT" Name="aktion" Value="Record">'
elif  [ "$RECORD" = "9" ]
then
  echo '<INPUT Type="SUBMIT" Name="aktion" Value="Download">'
  echo '<INPUT Type="SUBMIT" Name="aktion" Value="Delete">'
fi
echo '</TD></TR>'
p_buttons
echo '<TR><TD colspan="2">'

echo '<TABLE border="3" cellpadding="5">'
echo '<tr><th>Lfd.</th><th>Nummer</th><th>Name</th><th>Kanal</th>'
echo '<th>Dauer</th><th>Status</th>'
echo '<td><INPUT type="CHECKBOX" name="mark" Value="all"></td></tr>'
$ADMINBIN list $RAUM $PIN|/usr/bin/awk -F '!' '{
   if ($5 == "1")
   {
     printf("<tr bgcolor=\"#ff0000\">");
   }
   else
   {
     printf("<tr>");
   }
   printf("<td align=\"right\">%s</td>",$1);
   printf("<td>%s</td>",$2);
   printf("<td>%s</td>",$3);
   printf("<td>%s</td>",$4);
   printf("<td>%s</td>",$9);
   if      ($7 == "1")  { printf("<td>stumm</td>"); }
   else if ($8 == "1")  { printf("<td bgcolor=\"#ff0000\">spricht</td>"); }
   else if ($8 == "-1") { printf("<td>unbekannt</td>"); }
   else                 { printf("<td bgcolor=\"#00ff00\">bereit</td>"); }
   printf("<td><INPUT type=\"CHECKBOX\" name=\"mark\" Value=\"%s\"></td>",$1);
   
   printf("</tr>\n");
}'
echo '</TABLE>'

echo '</TD></TR>'
p_buttons

echo '</TABLE>'
echo '</FORM>'

p_endhtml
exit 0

