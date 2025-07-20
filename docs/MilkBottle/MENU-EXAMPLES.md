```bash
"This is a Welcome Message, Make sure your pdf file are in
the same folder as the PDFmilker"
# src/modules/PDFmilker/
# ----------------------

# input an option below to continue
"[1] Start PDF Extraction Process"
	if 1
		# Select an option
		[ENTER] Default, Image and Text
		[1] TEXT only
		[2] IMAGE only
		[0] GO BACK -> PDFmilker Main Menu
"[2] Options"
	if 2
		# Select to Toggle +ON or -OFF
		[1] [+]OVERWRITE allow re-milking existing slugs
		[2] LOG LEVEL [-]info|[-]debug|[+]quiet]
		[0] GO BACK -> PDFmilker Main Menu
"[0] BACK -> MilkBottle Main Menu"
	if 0
		# PLACEHOLDER FOR RETURNING TO MilkBottle Main Toolbox CLI Menu
"[q] QUIT APPLICATION"
	if q
		# QUIT APPLICATION
```
