DraveShot - schermafbeeldingen en schermopnames met annotaties
==============================================================

Dravenlock - lokaal en offline. Alles blijft op je eigen pc.

STARTEN
-------
Dubbelklik run.bat. De eerste keer installeert die zichzelf (Python 3.10 t/m
3.13 nodig). Werkt iets niet, gebruik start-debug.bat: die toont de fouten.

FFMPEG (nodig voor VIDEO)
-------------------------
Schermopname en het inbranden van annotaties in video gebeurt met ffmpeg.
- AUTOMATISCH: heb je nog geen ffmpeg, dan haalt DraveShot het bij het opstarten
  meteen zelf op (met een voortgangsbalk). Het komt in de map DraveShot-data en
  wordt daarna vanzelf gebruikt. (Kan ook via Instellingen: 'ffmpeg nu downloaden'.)
- HANDMATIG: heb je ffmpeg al (bijv. via DraveMedia), wijs het dan aan bij
  Instellingen, of zet ffmpeg.exe (en ffprobe.exe) naast de app of in
  DraveShot-data. Een complete uitgepakte ffmpeg-map in DraveShot-data mag ook;
  DraveShot zoekt nu ook in submappen (zoals bin).
Schermafbeeldingen (foto's) werken ook zonder ffmpeg.

SCHERMAFBEELDING
----------------
- Gebied vastleggen: sleep een kader over het scherm.
- Volledig scherm: legt het hele scherm vast (met instelbare vertraging).
- Annoteren met de knoppenbalk: tekst, pijl, lijn, rechthoek, ovaal, pen,
  markeerstift, vervagen (voor privacy) en bijsnijden. Kleur en dikte instelbaar.
- Opslaan als PNG/JPG of naar het klembord.

GROTER ZIEN EN VERSLEPEN
------------------------
Onder het voorbeeld staan knoppen: Uitzoomen (-), Passend, Inzoomen (+) en
100%. Je kunt ook zoomen met Ctrl + scrollwiel; bij inzoomen verschijnen
scrollbalken. Zet de knop op Kiezen/verplaatsen om tekst, pijlen en vormen
naar de juiste plek te slepen. Tekst wordt groot en met een donker plaatje
erachter getekend, zodat die altijd goed leesbaar is.

SCHERMOPNAME (VIDEO)
--------------------
- Opname starten (volledig scherm) of Opname (gebied). Tijdens het opnemen
  zie je een klein zwevend balkje met een Stop-knop; daarmee stop je de opname.
- Open de opname en teken er annotaties op. Selecteer een annotatie en stel
  met Van/Tot (seconden) in wanneer die in beeld is.
- Exporteren brandt de annotaties in een nieuwe videofile (.mp4).
- De tijdbalk onder de video laat je door de opname bladeren.

WAAR STAAN MIJN BESTANDEN
-------------------------
In de map DraveShot-data naast de app (opnames in DraveShot-data\opnames).
Portable: verplaats de hele map mee.

LET OP
------
Het vastleggen en opnemen van het scherm werkt op Windows. Op andere systemen
kun je wel bestaande afbeeldingen/video's openen en annoteren.

LOSSE .EXE MAKEN (optioneel)
----------------------------
Dubbelklik bouw-exe.bat. De .exe komt in de map dist (onefile). Zet ffmpeg.exe
naast de .exe voor de videofuncties.

SNELGIDS: druk op F1.
DONATIE (vrijwillig): https://paypal.me/roger076
CONTACT: service@dravenlock.nl
