#!/bin/bash
gmt --version
gmt gmtset MAP_FRAME_TYPE fancy
gmt gmtset MAP_FRAME_WIDTH 3p
gmt gmtset FONT_LABEL 7p,Helvetica
gmt gmtset FONT 7p,Helvetica
gmt gmtset PS_MEDIA a4
gmt gmtset MAP_ANNOT_OFFSET 1p
gmt gmtset MAP_LABEL_OFFSET 1p
gmt gmtset MAP_TICK_LENGTH_PRIMARY 2p
gmt gmtset MAP_TICK_LENGTH_SECONDARY 1p
gmt gmtset MAP_FRAME_PEN 1p
R=-166/-148/50/60
Rg=-170/-60/10/72
J=m0.2i
Jg=m0.008i
bdlst2=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/pb2002_steps.dat
PS=figure1.ps

stationfile=../data/station.txt
networkf=../data/network_long.txt
slipdir=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/rupturedatafile
rupturedir=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/AKruptures
terrane=../data/Alaska_terrane.dat
volcano=../data/volcano.csv
coast=100

## regional and station map
gmt grdcut @earth_relief_01m.grd -R$R -GAlaska.grd
gmt grdgradient Alaska.grd -A0 -Nt -Gint.grad
gmt makecpt -Cgeo -T-8000/5000 -D -Z  > 123.cpt
gmt grdimage -R$R -J$J Alaska.grd -C123.cpt -Iint.grad -Y5i -K  -P > $PS
gmt pscoast -R$R -J$J -W0.5p,"#444444" -A$coast -Df -K -O >> $PS

## plot trench
grep NA\/PA $bdlst2 | awk '{print $3,$4}' | gmt psxy -J -R -W2 -O -K >> $PS

## rupture zones
gmt psxy -R -J$J  $rupturedir/1946davies.lin -W1,black,- -: -h4 -O -K  >> $PS
gmt psxy -R -J$J  $rupturedir/1948davies.lin -W1,black,- -: -h4 -O -K  >> $PS
gmt psxy -R -J$J  $rupturedir/1957davies.lin -W1,black,- -: -h4 -O -K  >> $PS
gmt psxy -R -J$J  $rupturedir/1964davies.lin -W1,black,- -: -h4 -O -K  >> $PS
gmt psxy -R -J$J  $slipdir/far_eastern_1m.gmtlin -W1,black,- -h4 -O -K  >> $PS

# plot terrane
gmt psxy -R -J$J  $terrane -W1,black -O -K  >> $PS

# network
echo -164 56.4 -166 60 | gmt psxy -R$R -J$J -Sr+s -Gwhite -W1p -K -O >> $PS
i=0
for net in `awk '{print $1}' $networkf`
do
    color=`awk '$1=="'$net'" {print $3}' netcolor_ala.txt`
    shape=`awk '$1=="'$net'" {print $2}' netcolor_ala.txt`
    echo $color $shape
    awk -F '|' '{print $1 "." $2, $4, $3}' $stationfile | grep "$net." | awk '{print $2, $3}' | \
    gmt psxy -R$R -J$J -S"$shape"6p -W0.5p,black -G$color -K -O >> $PS
    text=$net
    YOFF=`echo "3.3 - $i * 0.12" |bc`
    gmt pslegend -R$R -J$J -Dx-0.05i/"$YOFF"i+jBL -O -K >> $PS <<EOF
S 0.1i $shape 6p $color 0.5p 0.2i $net
EOF
    i=`echo $i + 1 | bc -l`
done


awk -F, '{print $11, $10}' $volcano | gmt psxy -R$R -J$J -St6p -W0.5p,black -Gred -K -O >> $PS

## cmt solutions and slip area for earthquakes from 2020-2021 & 2023
gmt grdcontour $slipdir/simeonof_slip.grd -C+1,1.5,2 -J$J -R$R -W1,"#E02514" -O -K >> $PS
echo -159.28 54.83 36 4.15 -3.23 -0.92 5.38 2.93 -1.65 27 X Y | gmt psmeca -J$J -R$R -Sm5p -G"#E02514" -K -O >> $PS
gmt grdcontour $slipdir/chignik_slip.grd -C+1,1.5,2 -J$J -R$R -W1,"#40A362" -O -K >> $PS
echo -157.32 55.40 30 1.03 -0.77 -0.26 2.39 1.37 -0.48 28 X Y | gmt psmeca -J$J -R$R -Sm5p -G"#40A362" -K -O >> $PS
echo -159.70 54.48 37 0.05 -0.52 0.46 1.87 0.70 2.15 27 X Y | gmt psmeca -J$J -R$R -Sm5p -G"#4E00F5" -K -O >> $PS
echo -160.90 54.44 32 4.30 -3.66 -0.64 5.11 2.75 -1.56 26 X Y | gmt psmeca -J$J -R$R -Sm5p -G"#DE7017" -K -O >> $PS
echo -149.12 56.22 34 0.24 -0.48 0.25 0.19 -0.36 0.79 28 X Y | gmt psmeca -J$J -R$R -Sm5p -G"black" -K -O >> $PS
echo -151 58 1964 | gmt pstext -J$J -R$R -F+a60+f9p -D0/0 -K -O >> $PS
echo -155 55.5 1938 | gmt pstext -J$J -R$R -F+a30+f9p -D0/0 -K -O >> $PS
echo -161.5 55 1948 | gmt pstext -J$J -R$R -F+a0+f9p -D0/0 -K -O >> $PS
echo -163 54 1946 | gmt pstext -J$J -R$R -F+a10+f9p -D0/0 -K -O >> $PS
echo -164 54.1 1957 | gmt pstext -J$J -R$R -F+a0+f9p -D0/0 -K -O >> $PS

## note all islands
echo -164.11 54.46 Unimak | gmt pstext -J$J -R$R -F+a35+f9p -D0/0 -K -O >> $PS
echo -161.70 55.13 Pavlof | gmt pstext -J$J -R$R -F+a35+f9p -D0/0 -K -O >> $PS
echo -160.05 55.06 Shumagin | gmt pstext -J$J -R$R -F+a40+f9p -D0/0 -K -O >> $PS
echo -156.70 56.06 Semidi | gmt pstext -J$J -R$R -F+a40+f9p -D0/0 -K -O >> $PS
echo -153.50 57.4912 Kodiak | gmt pstext -J$J -R$R -F+a45+f9p -D0/0 -K -O >> $PS
echo "a)" | gmt pstext -R$R -J$J -F+cBL+f13p -Dj0.05i/0.05i -K -O>> $PS

## note volcanos
echo -161.894 55.417 | gmt psxy -R$R -J$J -St6p -W0.5p,black -Gyellow -K -O >> $PS
echo -161.894 55.417 Pavlof | gmt pstext -J$J -R$R -F+a35+f9p -D0/0 -K -O >> $PS
echo -159.38 56.17 | gmt psxy -R$R -J$J -St6p -W0.5p,black -Gyellow -K -O >> $PS
echo -159.38 56.17 Veniaminof | gmt pstext -J$J -R$R -F+a35+f9p -D0/0 -K -O >> $PS
echo -158.17 56.88 | gmt psxy -R$R -J$J -St6p -W0.5p,black -Gyellow -K -O >> $PS
echo -158.17 56.88 Aniakchak | gmt pstext -J$J -R$R -F+a35+f9p -D0/0 -K -O >> $PS
echo -155.1 58.236 | gmt psxy -R$R -J$J -St6p -W0.5p,black -Gyellow -K -O >> $PS
echo -155.1 58.236 Trident | gmt pstext -J$J -R$R -F+a35+f9p -D0/0 -K -O >> $PS

echo -148 50 -154.6 51 | gmt psxy -R$R -J$J -Sr+s -Gwhite -W1p -K -O >> $PS
gmt psscale -R$R -J$J -D2.4i/0.25i+w1.1i/3p+h+e -C123.cpt -Ba4000f1000+l"Elevation(m)" -K -O >> $PS

gmt psbasemap -R$R -J$J -Bx5f1 -By2f1 -BWseN -K -O >> $PS 

## plot map for larger area
gmt pscoast -R$Rg -J$Jg -W0.25p -B0 -Ggrey -B+gwhite -A2000 -N1 -X2.72i -Y0.325i -K -O --MAP_FRAME_TYPE=plain >> $PS 
gmt psbasemap -R$Rg -J$Jg -D$R -F+p1.5p -O  -K --MAP_FRAME_TYPE=plain >> $PS



# gmt psconvert -A -P -Tf $PS
gmt psconvert -P -Tf $PS
rm gmt.* Alaska.grd int.grad $PS
rm cptfile.cpt 123.cpt
#open ./$PS
