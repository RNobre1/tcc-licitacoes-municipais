# Torna texto/comum/ visível para \usepackage e \addbibresource sem caminho relativo.
# Sem isto, o preâmbulo compartilhado só seria encontrado com caminho embutido no
# .tex, o que quebraria ao compilar de outro diretório.
$ENV{'TEXINPUTS'} = '../comum:' . ($ENV{'TEXINPUTS'} // '');
$ENV{'BIBINPUTS'} = '../comum:' . ($ENV{'BIBINPUTS'} // '');
