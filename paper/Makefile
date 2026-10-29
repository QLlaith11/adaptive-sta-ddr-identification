# Build the paper (no BibTeX step: the bibliography is inline). Requires a TeX Live installation.
main.pdf: main.tex ieeeconf.cls fig_paper_tracking.pdf fig_paper_traj.pdf
	pdflatex -interaction=nonstopmode main.tex
	pdflatex -interaction=nonstopmode main.tex

clean:
	rm -f *.aux *.log *.out *.toc
