#!/bin/bash
gmt --version
gmt gmtset MAP_FRAME_TYPE plain
gmt gmtset FONT_LABEL 12p, Times-Roman
gmt gmtset FONT_ANNOT_PRIMARY 12p,Times-Roman
gmt gmtset PS_MEDIA a2
gmt gmtset MAP_TITLE_OFFSET 1.5p
gmt gmtset MAP_TICK_LENGTH_PRIMARY 10p
gmt gmtset MAP_TICK_LENGTH_SECONDARY 5p
gmt gmtset MAP_TICK_PEN_PRIMARY 1.5p
gmt gmtset MAP_TICK_PEN_SECONDARY 1p
R=-164/-148/50/60
Rg=-170/-60/10/72
J=m0.2i
Jg=m0.01i
PS=~/Documents/plot/alaska.ps

slipdir=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/rupturedatafile
rupturedir=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/AKruptures
bdlst2=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/pb2002_steps.dat
catf=/mnt/scratch/jieyaqi/alaska_new/catalog.txt


gmt pscoast -R$R -J$J -Glightgray -W0.5p,darkgrey -Swhite -A1000 -K > $PS
# gmt psmeca earthquake.dat -J$J -R$R -Sm7p -Z234.cpt -K -O >> $PS

# gmt psxy eastern_1m.gmtlin -R -J$J -W3p,red,- -V -N -O -P -K -m >> $PS_OUT
# gmt psxy -R -J$J  $rupturedir/1938davies.lin -W1,black -: -h4 -O -K  >> $PS
gmt psxy -R -J$J  $rupturedir/1946davies.lin -W1,black -: -h4 -O -K  >> $PS
gmt psxy -R -J$J  $rupturedir/1948davies.lin -W1,black -: -h4 -O -K  >> $PS
gmt psxy -R -J$J  $rupturedir/1957davies.lin -W1,black -: -h4 -O -K  >> $PS
gmt psxy -R -J$J  $rupturedir/1964davies.lin -W1,black -: -h4 -O -K  >> $PS
gmt grdcontour $slipdir/simeonof_slip.grd -C+1 -J$J -R$R -W1,black -O -K >> $PS
gmt psxy -R -J$J  $slipdir/far_eastern_1m.gmtlin -W1,black -h4 -O -K  >> $PS
gmt grdcontour $slipdir/chignik_slip.grd -C+1 -J$J -R$R -W1,black -O -K >> $PS
grep NA\/PA $bdlst2 | awk '{print $3,$4}' | gmt psxy -J -R -W2 -O -K >> $PS

gmt psbasemap -R$R -J$J -Bx5f1 -By2f1 -BWseN -K -O >> $PS 

rm gmt.*

gmt psconvert -A -P -Tf $PS

#open ./$PS
