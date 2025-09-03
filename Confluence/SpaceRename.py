import os

######################################################################
# Enter Space Key in CAPS and the entities.xml location directory
######################################################################
inputOldKeyL = ''
inputNewKeyL = ''
exportFolder = r''
######################################################################
######################################################################

oldKeyL = inputOldKeyL.lower()
newKeyL = inputNewKeyL.lower()
oldKeyU = oldKeyL.upper()
newKeyU = newKeyL.upper()

fileIn = os.path.join(exportFolder, 'entities.xml')
fileOut = os.path.join(exportFolder, 'entities2.xml')

with open(fileIn, 'r', encoding='utf-8') as f:
    fileContent = f.read()

replacements = [
    (f"<property name=\"lowerDestinationSpaceKey\"><![CDATA[{oldKeyL}]]></property>",
     f"<property name=\"lowerDestinationSpaceKey\"><![CDATA[{newKeyL}]]></property>"),
    (f"<property name=\"lowerKey\">![CDATA[{oldKeyL}]]></property>",
     f"<property name=\"lowerKey\">![CDATA[{newKeyL}]]></property>"),
    (f"[{oldKeyU}]", f"[{newKeyU}]"),
    (f"[{oldKeyL}]", f"[{newKeyL}]"),
    (f"spaceKey={oldKeyU}", f"spaceKey={newKeyU}"),
    (f"spaceKey={oldKeyL}", f"spaceKey={newKeyL}"),
    (f"[{oldKeyU}:", f"[{newKeyU}:"),
    (f"key={oldKeyU}]", f"key={newKeyU}]"),
    (f"<spaceKey>{oldKeyU}</spaceKey>", f"<spaceKey>{newKeyU}</spaceKey> "),
    (f"ri:space-key=\"{oldKeyU}\"", f"ri:space-key=\"{newKeyU}\""),
    (f"ri:space-key={oldKeyU}", f"ri:space-key={newKeyU}"),
    (f"<ac:parameter ac:name=\"spaces\">{oldKeyU}</ac:parameter>",
     f"<ac:parameter ac:name=\"spaces\">{newKeyU}</ac:parameter>"),
    (f"<ac:parameter ac:name=\"spaceKey\">{oldKeyU}</ac:parameter>",
     f"<ac:parameter ac:name=\"spaceKey\">{newKeyU}</ac:parameter>")
]

afterReplace = fileContent
for old, new in replacements:
    afterReplace = afterReplace.replace(old, new)

with open(fileOut, 'w', encoding='utf-8') as f:
    f.write(afterReplace)

os.rename(fileIn, os.path.join(exportFolder, 'entities_old.xml'))
os.rename(fileOut, os.path.join(exportFolder, 'entities.xml'))
