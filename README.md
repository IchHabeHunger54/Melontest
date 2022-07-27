# Melonenbot

Dies ist das offizielle GitHub-Repository für den Melonenbot. Der Melonenbot wurde exklusiv für den #TeamMelone-Server
in der Programmiersprache Python entwickelt. Tritt dem Server hier bei:
[https://discord.gg/teammelone](https://discord.gg/teammelone "https://discord.gg/teammelone")

## Bugs und neue Features

Sollte dir ein Bug aufgefallen sein, melde diesen bitte auf dem Discord. Solltest du einen Vorschlag für ein neues
Feature des Melonenbots haben, melde dies ebenfalls auf dem Discord.

## Lizenz

Der Code des Bots darf gemäß der MIT-Lizenz frei weiter verwendet werden. Wir würden aber darum bitten, uns angemessene
Credits zu geben, z.B. durch das Hinzufügen eines Kommentars in diesem oder einem ähnlichen Format:

```python
# Code developed with inspiration from: https://github.com/IchHabeHunger54/Melontest/blob/master/main.py
```

## Setup

Um den Melonenbot selbst zum Laufen zu bringen, werden folgende Dinge benötigt:

- Eine funktionsfähige Python-IDE (wir empfehlen PyCharm oder IntelliJ IDEA mit Python-Plugin)
- Python 3 (wir kompilieren gegen unterschiedliche Python 3.9-Versionen, allerdings funktionieren möglicherweise auch
  ältere Versionen von Python 3; Python 2.x funktioniert nicht)
- Das `discord.py`-Package
- ~~Das `mysql-connector-python`-Package~~ Das `psycopg2`-Package

Um den Melonenbot zu starten, einfach `main.py` laufen lassen. Achtung: Die Konfiguration (`config.json`) muss händisch
mit einem Token versehen werden; wir stellen nur einen Dummy bereit, da sonst der Token öffentlich werden würde.

## Codedesign

Für diejenigen, die den Code verstehen wollen, werden im Folgenden die wichtigsten Designprinzipien des Codes erklärt.

Das Hauptziel war es, den Bot modular zu gestalten. Das bedeutet, dass wir den Code, der z.B. auf Commands reagiert, in
Modulklassen ausgelagert haben. In `main.py` werden daher nur der Bot selbst, die Config (mehr dazu gleich), die
einzelnen Module sowie die Events initialisiert.

Alle Module erben von der Klasse `Module` (zu finden in `module.py`). Diese stellt leere Eventhandler-Methoden bereit,
die in Subklassen (zu finden in `modules.py`) implementiert werden können. In `main.py` wird dann über alle Module
iteriert, und jedes Modul führt seinen individuellen Eventhandler aus.

Die Config ist das zweite große Designprinzip des Bots. Beim Starten des Bots werden alle Konfigurationen aus einem File
namens `config.json` gelesen. Dabei wird ein Singleton-Pattern verwendet, d.h. es gibt nur ein einziges Config-Objekt,
das alle Konfigurationen speichert. Die Config wird dann standardmäßig jedem Modul als Parameter übergeben. Inhalt der
Config sind alle Kanal-IDs, Rollen-IDs, Datenbankwerte, Texte usw.

Die Config hat außerdem einige Werte doppelt - aktiviert oder deaktiviert wird die Verwendung der alternativen Werte
(mit `debug_`-Präfix) durch den `debug`-Wert. Dies hat den Grund, dass die Entwicklung des Bots auf einem eigens dafür
eingerichteten Server stattfindet, der logischerweise andere Kanal- und Rollen-IDs hat.

## Entstehungsgeschichte

Der Bot wurde ursprünglich von Detektiv Alex in JavaScript mit dem `discord.js`-Framework geschrieben. Mit der Zeit
kamen mehr Features hinzu, die teilweise in anderen Sprachen - Python mit dem `discord.py`-Framework und Java mit
dem `Java Discord API`-Framework - geschrieben waren.

Als sich Detektiv Alex aus der aktiven Entwicklung zurückzog und die Teamleitung für den Bot an IchHabeHunger54 übergab,
wurde die Entscheidung getroffen, den Bot, der zu diesem Zeitpunkt hauptsächlich in JavaScript, teilweise auch in Python
geschrieben war, von Grund auf neu zu entwickeln. Einige Features wurden an das damals neu erschienene Automod-Feature
von Discord ausgelagert, der Rest wurde vollständig in Python implementiert.

Aktuelle Entwickler des Bots sind IchHabeHunger54 und TryOne.
