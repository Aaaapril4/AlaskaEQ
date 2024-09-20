#!/bin/bash
gmt --version
gmt gmtset MAP_FRAME_TYPE fancy
gmt gmtset MAP_FRAME_WIDTH 3p
gmt gmtset FONT_LABEL 7p, Times-Roman
gmt gmtset FONT 7p,Times-Roman
gmt gmtset PS_MEDIA a4
gmt gmtset MAP_ANNOT_OFFSET 1p
gmt gmtset MAP_LABEL_OFFSET 1p
gmt gmtset MAP_TICK_LENGTH_PRIMARY 2p
gmt gmtset MAP_TICK_LENGTH_SECONDARY 1p
gmt gmtset MAP_FRAME_PEN 1p
R=-164/-148/50/60
Rg=-170/-60/10/72
J=m0.2i
Jg=m0.008i
bdlst2=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/pb2002_steps.dat
PS=figureS3.ps

stationfile=../data/station.txt
networkf=/mnt/scratch/jieyaqi/alaska/network.txt
slipdir=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/rupturedatafile
rupturedir=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/AKruptures
seisf1=../data/events_2month.csv
seisf2=/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_v1/catalogs_tomodd.csv
seisf3=/mnt/scratch/jieyaqi/alaska/final/eqt_2month/catalogs_tomodd.csv
seisf4=/mnt/scratch/jieyaqi/alaska/final/pntf_tonga/catalogs_tomodd.csv
cmtf=../data/cmt.csv
terrane=../data/Alaska_terrane.dat
coast=100

## regional and station map
gmt grdcut @earth_relief_01m.grd -R$R -GAlaska.grd
gmt grdgradient Alaska.grd -A0 -Nt -Gint.grad

# plot AEC
gmt pscoast -R$R -J$J -Glightgray -W0.5p,"#444444" -Swhite -A$coast -Df -Y4i -K -P >> $PS
# gmt psmeca earthquake.dat -J$J -R$R -Sm7p -Z234.cpt -K -O >> $PS

grep NA\/PA $bdlst2 | awk '{print $3,$4}' | gmt psxy -J -R -W2 -O -K >> $PS
gmt makecpt -Cjet -T0/250/50 -Iz -Z > cptfile.cpt
awk -F, 'NR>1 {print $3, $4, $5}' $seisf1 | gmt psxy -R$R -J$J -Sc2p -Ccptfile.cpt -K -O >> $PS
echo -148 50 -154.6 51 | gmt psxy -R$R -J$J -Sr+s -Gwhite -W1p -t30 -K -O >> $PS
gmt psscale -R$R -J$J -D1.99i/0.25i+w1.1i/3p+h+e -Ccptfile.cpt -Ba50f10+l"Depth(km)" -K -O >> $PS
gmt pscoast -R$R -J$J -W0.5p,"#444444" -A$coast -Df -K -O >> $PS
echo "A) Reference" | gmt pstext -R$R -J$J -F+cBL+f10p -Dj0.05i/0.05i -K -O>> $PS
gmt psbasemap -R$R -J$J -Bx5f1 -By2f1 -BWseN -O -K >> $PS 


# plot pntf alaska v1
gmt pscoast -R$R -J$J -Glightgray -W0.5p,"#444444" -Swhite -A$coast -Df -X3.42i -K -O >> $PS
# gmt psmeca earthquake.dat -J$J -R$R -Sm7p -Z234.cpt -K -O >> $PS

grep NA\/PA $bdlst2 | awk '{print $3,$4}' | gmt psxy -J -R -W2 -O -K >> $PS
gmt makecpt -Cjet -T0/250/50 -Iz -Z > cptfile.cpt
awk -F, 'NR>1 {print $2, $3, $4}' $seisf2 | gmt psxy -R$R -J$J -Sc2p -Ccptfile.cpt -K -O >> $PS
gmt pscoast -R$R -J$J -W0.5p,"#444444" -A$coast -Df -K -O >> $PS
echo "B) PhaseNet-TF Alaska" | gmt pstext -R$R -J$J -F+cBL+f10p -Dj0.05i/0.05i -K -O>> $PS
gmt psbasemap -R$R -J$J -Bx5f1 -By2f1 -BwseN -O -K >> $PS 


# plot eqt 
gmt pscoast -R$R -J$J -Glightgray -W0.5p,"#444444" -Swhite -A$coast -Df -X-3.42i -Y-3.73i -K -O >> $PS
# gmt psmeca earthquake.dat -J$J -R$R -Sm7p -Z234.cpt -K -O >> $PS

grep NA\/PA $bdlst2 | awk '{print $3,$4}' | gmt psxy -J -R -W2 -O -K >> $PS
gmt makecpt -Cjet -T0/250/50 -Iz -Z > cptfile.cpt
awk -F, 'NR>1 {print $2, $3, $4}' $seisf3 | gmt psxy -R$R -J$J -Sc2p -Ccptfile.cpt -K -O >> $PS
gmt pscoast -R$R -J$J -W0.5p,"#444444" -A$coast -Df -K -O >> $PS
echo "C) EQTransformer" | gmt pstext -R$R -J$J -F+cBL+f10p -Dj0.05i/0.05i -K -O>> $PS
gmt psbasemap -R$R -J$J -Bx5f1 -By2f1 -BWsen -O -K >> $PS 


# plot pntf tonga
gmt pscoast -R$R -J$J -Glightgray -W0.5p,"#444444" -Swhite -A$coast -Df -X3.42i -K -O >> $PS
# gmt psmeca earthquake.dat -J$J -R$R -Sm7p -Z234.cpt -K -O >> $PS

grep NA\/PA $bdlst2 | awk '{print $3,$4}' | gmt psxy -J -R -W2 -O -K >> $PS
gmt makecpt -Cjet -T0/250/50 -Iz -Z > cptfile.cpt
awk -F, 'NR>1{print $2, $3, $4}' $seisf4 | gmt psxy -R$R -J$J -Sc2p -Ccptfile.cpt -K -O >> $PS
gmt pscoast -R$R -J$J -W0.5p,"#444444" -A$coast -Df -K -O >> $PS
echo "D) PhaseNet-TF Tonga" | gmt pstext -R$R -J$J -F+cBL+f10p -Dj0.05i/0.05i -K -O>> $PS
gmt psbasemap -R$R -J$J -Bx5f1 -By2f1 -Bwsen -O >> $PS 


# gmt psconvert -A -P -Tf $PS
gmt psconvert -P -Tf $PS
rm gmt.* Alaska.grd int.grad $PS
rm cptfile.cpt
#open ./$PS
