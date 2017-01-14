/* --- Dieses Programm dient dazu, das CLI von Asterisk nur für den       --- */
/* --- meete-Befehl auszuführen. Zur Authorisation wird die Admini-       --- */
/* --- strator-PIN des Konferenzraumes geprüft. Dem Programm muss mittels --- */
/* --- Set-UID- / Set-GID-Bit der Zugriff auf die Asterisk-Konfiguration  --- */
/* --- und den Socket zur Steuerung gewährt werden                        --- */
/* --- Author: Lothar Krauß (mailto: pirat@lkrauss.de)                    --- */
/* --- Lizenz: CC-BY                                                      --- */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>

/* --- Konstanten zum Auffinden der Asterisk-Dateien --- */
#define ASTBIN  "/opt/asterisk/sbin/asterisk"
#define ASTMEET "/opt/asterisk/etc/asterisk/meetme.conf"
#define ASTICE  "/opt/asterisk/ices"
#define ASTOUT  "/opt/asterisk/var/spool/asterisk/outgoing"
#define ASTMON  "/opt/asterisk/var/spool/asterisk/monitor"
#define ICEPWD  "***passwort***"

/* --- Ein Buffer zum Einlesen einer Zeile --- */
char wBuf[512];

/* --- Liest eine Zeile aus f in s (max size-1 Bytes + Null-Byte) --- */
/* --- und schneidet Leerzeichen und Tabs vorne und hinten ab     --- */
/* --- Ergebnis: NULL = Fehler/Dateiende, ansonsten s             --- */
char *readTrim(char *s, int size, FILE *f)
{
  int i1,i2,j;
  if (fgets(s,size,f)==NULL) return(NULL);
  for (i1=0; strchr(" \t\r\n",s[i1])!=NULL; i1++);
  for (i2=strlen(s); i2>=i1 && strchr(" \t\r\n",s[i2-1])!=NULL; i2--);
  if (i1==0)
     j=i2;
  else
     for (j=0; i1<i2; j++,i1++) s[j]=s[i1];
  s[j]=0;
  return(s);
}

/* --- Testet, ob "pin" die korrekte Admin PIN von Raum "room" ist --- */
/* --- Ergebnis: 0 = Raum oder PIN falsch                          --- */
/* ---           1 = Raum und PIN passen zuammen                   --- */
int checkAdmin(int room, int pin)
{
  FILE *f;
  int  i1,i2,flag_found;
  int  room1,pin1;

  if ((f=fopen(ASTMEET,"r"))==NULL) return(0);

  /* --- Suche eine Zeile "[rooms]" --- */
  strcpy(wBuf,"");
  flag_found=0;
  for (flag_found=0; !flag_found && readTrim(wBuf,sizeof(wBuf),f)!=NULL; )
  {
    if (!strcmp(wBuf,"[rooms]")) flag_found=1;
  }
  if (!flag_found)
  {
    fclose(f);
    return(0);
  }

  /* --- Suche die Raumnummer, Ende spaetestens bei naechster Sektion --- */
  for (flag_found=0; !flag_found && readTrim(wBuf,sizeof(wBuf),f)!=NULL; )
  {
    /* --- Zeile lautet "conf => raum,pin1,pin2" --- */
    if (strncmp(wBuf,"conf",4)) continue;
    for (i1=4; wBuf[i1]==' ' || wBuf[i1]=='\t'; i1++);
    if (strncmp(wBuf+i1,"=>",2))  continue;
    for (i1+=2; wBuf[i1]==' '||wBuf[i1]=='\t'; i1++);

    /* --- Lese Raumnummer --- */
    for (room1=0; isdigit(wBuf[i1]); i1++) room1=10*room1+(int)(wBuf[i1]-'0');
    if (room1!=room) continue;

    /* --- Ueberspringe "," --- */
    for (; wBuf[i1]==' '||wBuf[i1]=='\t'; i1++);
    if (wBuf[i1]!=',') continue;
    for (i1++ ; wBuf[i1]==' '||wBuf[i1]=='\t'; i1++);

    /* --- Ueberspringe User-PIN --- */
    for (; isdigit(wBuf[i1]); i1++);

    /* --- Ueberspringe "," --- */
    for (; wBuf[i1]==' '||wBuf[i1]=='\t'; i1++);
    if (wBuf[i1]!=',') continue;
    for (i1++ ; wBuf[i1]==' '||wBuf[i1]=='\t'; i1++);

    /* --- Lese Admin-PIN --- */
    for (pin1=0; isdigit(wBuf[i1]); i1++) pin1=10*pin1+(int)(wBuf[i1]-'0');
    flag_found=1;
  }

  if (!flag_found)
  {
    fclose(f);
    return(0);
  }

  fclose(f);

  if (pin!=pin1) return(0);
  return(1);
}

void showHelp()
{
  printf("Aufruf: meetmeadmin Befehl Raumnr PIN [Usernr] [Usernr]...\n");
  printf("Befehl: list     Listet die Teilnehmer der Konferenz\n");
  printf("Befehl: lock     Schliesst die Konferenz\n");
  printf("Befehl: unlock   Oeffnet die Konferenz wieder\n");
  printf("Befehl: mute     Schaltet die angegebenen Teilnehmer stumm\n");
  printf("Befehl: unmute   Schaltet die angegebenen Teilnehmer wieder frei\n");
  printf("Befehl: kick     Wirft die angegebenen Teilnehmer aus der Konferenz\n");
  printf("Befehl: stream   Startet einen Icecast Stream\n");
  printf("Befehl: test     Keine Ausgabe, Testet nur Gueltigkeit von Raum und PIN\n");
  printf("Returncode: 0=Erfolg, 1=Fehler\n");
}

/* --- Fuehrt einen Befehl aus (User darf NULL sein) --- */
void Cmd(char *sCmd, char *sRoom, char *sUser)
{
  int i,s;

  /* --- Plausi-Checks --- */
  if (sCmd==NULL||sRoom==NULL) return;
  i=7+strlen(sCmd)+1+strlen(sRoom)+1;
  if (sUser!=NULL) i=i+1+strlen(sUser);
  if (i>sizeof(wBuf)) return;

  strcpy(wBuf,"meetme ");
  strcat(wBuf,sCmd);
  strcat(wBuf," ");
  strcat(wBuf,sRoom);
  if (sUser!=NULL) { strcat(wBuf," "); strcat(wBuf,sUser); }
  i=fork();
  if (i==-1) return;
  if (i>0)
  {
    execl(ASTBIN,ASTBIN,"-r","-x",wBuf,NULL);
    exit(0);
  }
  else
  {
    waitpid(i,&s,0);
  }
}

void Stream(int iRoom)
{
   FILE *f;

   /* --- ices2-Konfiguration aufbauen --- */
   sprintf(wBuf,"%s/raum%04i.xml",ASTICE,iRoom);
   if ((f=fopen(wBuf,"w"))==NULL) return;
   chmod(wBuf,S_IREAD|S_IWRITE);
   fprintf(f,"<?xml version=\"1.0\"?>\n");
   fprintf(f,"<ices>\n");
   fprintf(f,"  <background>0</background>\n");
   fprintf(f,"  <logpath>/opt/asterisk/var/log/asterisk</logpath>\n");
   fprintf(f,"  <logfile>ices.log</logfile>\n");
   fprintf(f,"  <loglevel>1</loglevel>\n");
   fprintf(f,"  <consolelog>0</consolelog>\n");
   fprintf(f,"  <stream>\n");
   fprintf(f,"    <metadata>\n");
   fprintf(f,"      <name>Raum %04i</name>\n",iRoom);
   fprintf(f,"      <genre>Telefonkonferenz</genre>\n");
   fprintf(f,"      <description>Telefonkonferenz Piratenpartei Hessen Raum %04i</description>\n",iRoom);
   fprintf(f,"      <url>http://www.piratenpartei-hessen.de</url>\n");
   fprintf(f,"    </metadata>\n");
   fprintf(f,"    <input>\n");
   fprintf(f,"      <module>stdinpcm</module>\n");
   fprintf(f,"      <param name=\"rate\">8000</param>\n");
   fprintf(f,"      <param name=\"channels\">1</param>\n");
   fprintf(f,"    </input>\n");
   fprintf(f,"    <instance>\n");
   fprintf(f,"      <hostname>localhost</hostname>\n");
   fprintf(f,"      <port>8000</port>\n");
   fprintf(f,"      <password>%s</password>\n",ICEPWD);
   fprintf(f,"      <mount>/raum%04i.ogg</mount>\n",iRoom);
   fprintf(f,"      <yp>0</yp>\n");
   fprintf(f,"      <encode>\n");
   fprintf(f,"        <quality>0</quality>\n");
   fprintf(f,"        <samplerate>8000</samplerate>\n");
   fprintf(f,"        <channels>1</channels>\n");
   fprintf(f,"      </encode>\n");
   fprintf(f,"      <downmix>0</downmix>\n");
   fprintf(f,"    </instance>\n");
   fprintf(f,"  </stream>\n");
   fprintf(f,"</ices>\n");
   fclose(f);

   /* --- Asterisk Call File aufbauen --- */
   sprintf(wBuf,"%s/raum%04i.call",ASTOUT,iRoom);
   if ((f=fopen(wBuf,"w"))==NULL) return;
   fprintf(f,"Channel: LOCAL/81%04i\n",iRoom);
   fprintf(f,"MaxRetries: 1\n");
   fprintf(f,"RetryTime: 15\n");
   fprintf(f,"WaitTime: 30\n");
   fprintf(f,"Application: Ices\n");
   fprintf(f,"Data: %s/raum%04i.xml\n",ASTICE,iRoom);
   fprintf(f,"Callerid: Stream <0>\n");
   fprintf(f,"AlwaysDelete: Yes\n");
   fclose(f);
}

void DelRecord(int iRoom)
{
   sprintf(wBuf,"%s/raum%04i.gsm",ASTMON,iRoom);
   unlink(wBuf);
}

void Record(int iRoom)
{
   FILE *f;
   /* --- Asterisk Call File aufbauen --- */
   sprintf(wBuf,"%s/raum%04i.call",ASTOUT,iRoom);
   if ((f=fopen(wBuf,"w"))==NULL) return;
   fprintf(f,"Channel: LOCAL/81%04i\n",iRoom);
   fprintf(f,"MaxRetries: 1\n");
   fprintf(f,"RetryTime: 15\n");
   fprintf(f,"WaitTime: 30\n");
   fprintf(f,"Application: Record\n");
   fprintf(f,"Data: %s/raum%04i.gsm|0|18000|x\n",ASTMON,iRoom);
   fprintf(f,"Callerid: Record <0>\n");
   fprintf(f,"AlwaysDelete: Yes\n");
   fclose(f);
}

int main(int argc, char **argv)
{
  char *sCmd,*sRoom,*sPin,*sUser;
  int iRoom,iPin;
  int i,j;

  if (argc<4) { showHelp(); exit(1); }

  sCmd=argv[1];

  sRoom=argv[2];
  for (i=0; isdigit(sRoom[i]); i++);
  if (i<1 || i>4 || sRoom[i]!=0) { exit(1); }
  iRoom=atoi(sRoom);

  sPin =argv[3];
  for (i=0; isdigit(sPin[i]); i++);
  if (i<1 || i>10 || sPin[i]!=0) { exit(1); }
  iPin =atoi(sPin);

  if (iRoom<1000||iRoom>9999||iPin<1) { exit(1); }

  if (!checkAdmin(iRoom,iPin))
  {
    exit(1);
  }

  if (!strcmp(sCmd,"test")) exit(0);

  if (!strcmp(sCmd,"lock")  ||
      !strcmp(sCmd,"unlock")  )
  {
    Cmd(sCmd,sRoom,NULL);
    exit(0);
  }

  if (!strcmp(sCmd,"list"))
  {
    Cmd(sCmd,sRoom,"concise");
    exit(0);
  }

  if (!strcmp(sCmd,"mute")   ||
      !strcmp(sCmd,"unmute") ||
      !strcmp(sCmd,"kick")     )
  {
    for (j=4; j<argc; j++)
    {
      sUser=argv[j];
      if (strcmp(sUser,"all"))
      {
        for (i=0; isdigit(sUser[i]); i++);
        if (i<1 || i>4 || sUser[i]!=0) { exit(1); }
      }
      Cmd(sCmd,sRoom,sUser);
    }
    return(0);
  }

  if (!strcmp(sCmd,"stream"))
  {
    Stream(iRoom);
    exit(0);
  }

  if (!strcmp(sCmd,"record"))
  {
    Record(iRoom);
    exit(0);
  }
  if (!strcmp(sCmd,"delrecord"))
  {
    DelRecord(iRoom);
    exit(0);
  }

  showHelp();
  exit(1);
}
