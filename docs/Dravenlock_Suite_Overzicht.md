# Dravenlock — Overzicht van de complete suite

> Bewaar dit bestand. Upload het in een nieuw gesprek zodat de volledige line-up
> meteen bekend is (handig om geen dubbele ideeën voor te stellen en te zien wat
> ergens op voortbouwt).

## Het Dravenlock-recept
Lokaal en **offline**, geen cloud/account · **toegankelijk** (grote tekst, hoog
contrast, schermlezer-vriendelijk, volgt de computertaal NL/EN, denkt aan EU
EAA/WCAG AA) · **donationware** (service@dravenlock.nl — paypal.me/roger076) ·
huisstijl donker (#0e0e11) + zilver + staalblauw (#6fa3d6), PyQt6 · geleverd als
zip + projectdossier · vaste launchers (Python 3.13→3.10, val-terug `python`,
`--only-binary=:all:`) · vervangt vaak iets duurs of cloud-achtigs.

---

## Bestaande apps (gebouwd)

> Volledige line-up per 17 juni 2026 (op basis van Rogers eigen mappenoverzicht):
> **31 apps**, plus de zojuist gebouwde DraveVault.

**Web & server**

| App | Wat het is | Vervangt / lijkt op |
|-----|------------|---------------------|
| **DraveServer** | Apache-webserver-manager (schrijft alle config zelf) | XAMPP-controlpanel |
| **DravePyServer** | Webserver-manager op een eigen pure-Python motor (cheroot) | XAMPP / eigen server |
| **DraveEdit** | WYSIWYG website-bouwer (HTML5) | webbouwers / Adobe |
| **DraveMaster** | Browser voor zijn man (D&D: dobbelsteen + links naar AI-tools) | - |
| **DravenlockBrowser** (DraveBrowser) | Browser met games/widgets; zware privacybescherming | - |
| **DravenCrawl** | Website-zoek-app | - |
| **DraveLink** | (eerdere app) | - |

**Toegankelijkheid**

| App | Wat het is | Vervangt / lijkt op |
|-----|------------|---------------------|
| **DraveZoom** | Schermvergrootglas | Windows-vergrootglas |
| **DraveRead** | Tekst-naar-spraak (voorlezen) | voorleessoftware |
| **DraveContrast** | WCAG-contrastchecker | - |

*(DraveZoom/DraveRead zijn vermoedelijk wat eerder "DraveLens/DraveText" heetten.)*

**D&D-tools (voor man/vriend)**

| App | Wat het is | Vervangt / lijkt op |
|-----|------------|---------------------|
| **DraveCodex** | Offline campagne-wiki | - |
| **DraveSheet** | Character sheets | - |
| **DraveTable** | DM-/initiatief-/HP-tracker | - |
| **DraveDice** | Dobbelroller | - |
| **DravePoort** | Launcher/portal die alle Drave-apps toont en start (voor zijn man) | PortableApps |

**Documenten & media**

| App | Wat het is | Vervangt / lijkt op |
|-----|------------|---------------------|
| **DravePDF** | Alles-in-een PDF-tool (gereedschap/maken/bewerken/ondertekenen) | Adobe (PDF) |
| **DraveForms** | PDF-formulieren invullen (dropdowns, tekst, vinkjes) | Adobe (formulieren) |
| **DraveNote** | Lokale Markdown-notities | - |
| **DraveTag** | Media-tags bewerken + bulk hernoemen | - |
| **DraveMedia** | Media-app (metadata, PWA) | - |
| **DraveConvert** | Lokale media-/bestandsconverter (audio/video/afbeeldingen) | online converters |
| **DraveMotion** | Animatie-/video-editor | Magix |
| **DraveSound** | Muziek-app | Magix |
| **DraveStudio** | Beeldbewerking | Photoshop |
| **DraveVault** | Versleutelde wachtwoord-/notitiekluis (offline) - *gebouwd, v0.1* | cloud-wachtwoordmanagers |
| **DraveBackup** | Geplande lokale back-up/sync van mappen (sync/zip) - *gebouwd, v0.1* | cloud-back-up |
| **DraveShot** | Schermafbeeldingen + schermopname met annotaties - *gebouwd, v0.1* | ShareX / Snagit |

**Systeem & distributie**

| App | Wat het is | Vervangt / lijkt op |
|-----|------------|---------------------|
| **SysCare** | Systeemonderhoud/optimalisatie | IObit |
| **DraveExplorer** | Windows-bestandsverkenner | Windows Verkenner |
| **DraveUninstal** | Uninstaller die ook rest-rommel opruimt | Revo / IObit Uninstaller |
| **DravePurge** | Browser-privacy schoonmaken | CCleaner (privacy) |
| **dravesetup** | Maakt van een **.exe** een installer + uninstaller | - |
| **Pysetup_maker** | Installer maken vanuit een **.py**-bestand | - |

**Communicatie**

| App | Wat het is | Vervangt / lijkt op |
|-----|------------|---------------------|
| **DeskButler** | E-mailclient | BunzieBuddy / Incredimail |

## Patronen in de suite
- **Adobe/Magix de deur uit**: DraveStudio (Photoshop), DraveMotion + DraveSound
  (Magix), DraveForms (Adobe-formulieren).
- **Systeem & distributie**: SysCare (onderhoud), dravesetup + Pysetup_maker
  (installers vanaf .exe resp. .py).
- **Web & info**: DraveBrowser, DraveMaster, DravenCrawl, DraveEdit, DraveLink.
- **Communicatie/media**: DeskButler, DraveMedia.

## Openstaand op de actieve app
- **DraveEdit v0.18**: app-taal laten volgen van de computer (NL basis + EN,
  OS-detectie + handmatige override) — net als zijn andere apps. Die taallaag is
  daarna herbruikbaar in elke nieuwe Drave-app.

## Nog te maken
Geen openstaande builds - DraveBackup en DraveShot zijn deze ronde gebouwd (v0.1).
Nieuwe ideeën staan in **Dravenlock_Ideeen.md**. Vriend (D&D-master) levert mogelijk
nog meer aan.

---

*Aanvullen waar nodig; statussen (af / in ontwikkeling) per app kunnen later
toegevoegd worden.*
