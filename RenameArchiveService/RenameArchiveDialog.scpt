-- The output of this script is "true:", and then the selected directory name.
-- Output of anything else means the user clicked "Cancel" instead of selecting a directory, or there was an error.

set directoryNames to paragraphs of (system attribute "DIRECTORYNAMES")
set archiveName to (system attribute "ARCHIVENAME")
set selectedName to false

if (length of directoryNames) is not 0 then
	set selectedResult to choose from list directoryNames ¬
		with title "Rename Archive" ¬
		with prompt "Select a new name for " & archiveName & ":" ¬
		OK button name "Rename"
	if selectedResult is not false then
		set selectedName to item 1 of selectedResult
	end if
end if

if selectedName is not false then
	do shell script "echo true:" & quoted form of selectedName
else
	do shell script "echo false"
end if
