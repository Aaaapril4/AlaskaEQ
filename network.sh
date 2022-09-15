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
bdlst2=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/pb2002_steps.dat
PS=~/Documents/plot/network_ala.ps

stationfile=/mnt/scratch/jieyaqi/alaska/station.txt
networkf=/mnt/scratch/jieyaqi/alaska/network.txt
slipdir=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/rupturedatafile
seisf=/mnt/ufs18/nodr/home/jieyaqi/alaska/seismicity.txt
catf=/mnt/scratch/jieyaqi/alaska_new/catalog.txt


gmt grdcut @earth_relief_01m.grd -R$R -GAlaska.grd
gmt grdgradient Alaska.grd -A0 -Nt -Gint.grad

gmt makecpt -Cgeo -T-8000/5000 -D -Z  > 123.cpt

gmt grdimage -R$R -J$J Alaska.grd -C123.cpt -Iint.grad -K  > $PS

gmt pscoast -R$R -J$J -W0.5p,darkgrey -A1000 -K -O >> $PS
#gmt psmeca earthquake.dat -J$J -R$R -Sm7p -Z234.cpt -K -O >> $PS

#gmt psmeca earthquake2.dat -J$J -R$R -Sa7p -Z234.cpt -K -O >> $PS


# gmt psxy ~/Documents/earifts.xy -R$R -J$J -W1p/black -O -K >> $PS
# gmt psxy ~/Documents/tzcraton.xy -R$R -J$J -W1p/black -O -K>> $PS
# gmt psxy ~/Documents/volcano_africa.txt -R$R -J$J -St6p -Wblack -Gred -O -K >> $PS

gmt makecpt -Cseis -T0/300/20 -D > cptfile.cpt
# gmt psmeca earthquake.dat -J$J -R$R -Sm7p -Z234.cpt -K -O >> $PS
awk -F ',' 'NR>1{print $3, $2, $4}' $seisf | gmt psxy -R$R -J$J -Sc2p -Gblack -W0.1p,black -K -O >> $PS

i=0
for net in `awk '{print $1}' $networkf`
do
    color=`awk '$1=="'$net'" {print $3}' netcolor_ala.txt`
    shape=`awk '$1=="'$net'" {print $2}' netcolor_ala.txt`
    echo $color $shape
    awk -F '|' '{print $1 "." $2, $4, $3}' $stationfile | grep "$net." | awk '{print $2, $3}' | \
    gmt psxy -R$R -J$J -S"$shape"5p -W0.5p,black -G$color -K -O >> $PS
    text=$net
    YOFF=`echo "60 - $i * 1" |bc`
gmt pslegend -R$R -J$J -D-128/$YOFF/10 -O -K >> $PS <<EOF
S 0.1i $shape 5p $color 0.5p 0.2i $net
EOF
i=`echo $i + 1 | bc -l`
done



gmt psbasemap -R$R -J$J -Bx5f1 -By2f1 -BWseN -K -O >> $PS 

gmt grdcontour $slipdir/simeonof_slip.grd -C+1 -J$J -R$R -W1,red -O -K >> $PS
gmt grdcontour $slipdir/chignik_slip.grd -C+1 -J$J -R$R -W1,green -O -K >> $PS

#awk 'NR==1 {print $0}' $catf | gmt psmeca -J$J -R$R -Sm7p -Gred -K -O >> $PS
#awk 'NR==2 {print $0}' $catf | gmt psmeca -J$J -R$R -Sm7p -Ggreen -K -O >> $PS
#awk 'NR==3 {print $0}' $catf | gmt psmeca -J$J -R$R -Sm7p -Gblue -K -O >> $PS

grep NA\/PA $bdlst2 | awk '{print $3,$4}' | gmt psxy -J -R -W2 -O -K >> $PS

gmt pscoast -R$Rg -J$Jg -W0.25p -B0 -Ggrey -B+gwhite -A2000 -N1 -X2.05i -Y0.05i -K -O >> $PS 

gmt psbasemap -R$Rg -J$Jg -D$R -F+p1.5p -O  -K -P>> $PS 

# dx1 symbol size fill pen dx2 text 
gmt psscale -R$R -J$J -D0.5i/-0.5i/3i/0.1ih -C123.cpt -B3000 -K -O >> $PS

rm gmt.* Alaska.grd int.grad

gmt psconvert -A -P -Tf $PS

#open ./$PS
