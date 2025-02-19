#!/bin/bash
gmt --version
gmt gmtset MAP_FRAME_TYPE fancy
gmt gmtset MAP_FRAME_WIDTH 3p
gmt gmtset FONT 10p,Helvetica
gmt gmtset FONT_LABEL 10p,Helvetica
gmt gmtset PS_MEDIA a3
gmt gmtset MAP_TITLE_OFFSET 1p
gmt gmtset MAP_LABEL_OFFSET 1p
gmt gmtset MAP_ANNOT_OFFSET 1p
gmt gmtset MAP_TICK_LENGTH_PRIMARY 2p
gmt gmtset MAP_TICK_LENGTH_SECONDARY 1p
gmt gmtset MAP_TICK_PEN_PRIMARY 1p
gmt gmtset MAP_TICK_PEN_SECONDARY 0.5p
gmt gmtset MAP_FRAME_PEN 1p

seisf=/mnt/scratch/jieyaqi/alaska/alaska_long/catalogs_new.csv
terrane=../data/Alaska_terrane.dat
volcano=../data/volcano.csv
coast=100
width=20
PS=figure6.ps

gmt grdcut @earth_relief_03m.grd -R-166/-148/50/60 -Gtopo.grd
gmt makecpt -C"#6868FF","#FF6AAD" -T-9600,0 -Z > time.cpt

plot_cross_section() {
    depth="$7"
    staprojdis="$8"
    Xoff=$9
    Yoff=${10}
    w=${11}
    e=${12}
    s=${13}
    text=${14}
    echo $1 $2 $3 $4
    gmt project -C$1/$2 -E$3/$4 -G0.025 > lined
    
    volcano_d=`echo $5 $6 | gmt project -C$1/$2 -E$3/$4 -Q | awk '{print $3}'` 
    # topography
    gmt grdtrack lined -Gtopo.grd | awk '{print $1, $2, $4}' > tomolined.dat
    echo $1 $2 0 > temp
    awk 'NR==1{print '$1', '$2', $3}' tomolined.dat >> temp
    cat tomolined.dat >> temp 
    tail -n1 tomolined.dat | awk '{print '$3', '$4', $3}' >> temp
    echo $3 $4 0 >> temp
    mv temp tomolined.dat
    python3 calculate_dist.py tomolined.dat 0 1 $1 $2 $volcano_d> temp
    mv temp tomolined.dat
    mindist=`head -n1 tomolined.dat | awk '{print $1}'`
    maxdist=`tail -n1 tomolined.dat | awk '{print $1}'`

    R1=-60/60/0/2
    R2=-60/60/0/$depth
    J1=x0.03i/0.15i
    J2=x0.03i/-0.03i
    Y=`echo $depth \* 0.03 | bc -l`
    awk '{print $1, $4*0.001}' tomolined.dat | gmt psxy -R$R1 -J$J1 -W1p -X"$Xoff"i -Y"$Yoff"i -K -O >> $PS

    awk -F, '{print $11, $10}' $volcano > temp
    python3 staclose.py temp $1/$2/$3/$4 $staprojdis 0 1 $volcano_d > staXY
    awk '{print $1, 0.2}' staXY | gmt psxy -R$R1 -J$J1 -St8p -W0.5p,black -Gred -K -O  >> $PS

    gmt psbasemap -R$R1 -J$J1 -By1f0.5+l'Topo(km)' -Bw${e}s -K -O >> $PS
    echo $text\' | gmt pstext -R$R1 -J$J1 -F+cTL+f13p -Dj0.03i/0i -K -O>> $PS
    echo $text | gmt pstext -R$R1 -J$J1 -F+cTR+f13p -Dj0.03i/0i -K -O>> $PS

    awk '{print $1, $4*-0.001}' tomolined.dat | gmt psxy -R$R2 -J$J2 -W1p,darkgray -Gdarkgray -Y-"$Y"i -K -O >> $PS

    #seismicity
    /mnt/home/jieyaqi/anaconda3/envs/seis/bin/python3 staclose.py $seisf $1/$2/$3/$4 $staprojdis 1 2 $volcano_d , > staXY

    # background
    awk -F, 'NR>1{print $1, $7, $14, 1, 1}' staXY | gmt psxy -R$R2 -J$J2 -Sc1p -Ctime.cpt -E+w0p+p0.6+cl -K -O >> $PS
    gmt psbasemap -R$R2 -J$J2 -By10f2 -Bx50f10 -Bw${s}${e} -Bx+l'Distance(km)' -By+l'Depth(km)' -K -O >> $PS

    rm tomolined.dat
    rm lined
    rm staXY
    rm temp
}


R=-162.894/-160.894/54.417/56.417
J=m0.5i

## regional and station map
gmt grdcut @earth_relief_01m.grd -R$R -GAlaska.grd
gmt grdgradient Alaska.grd -A0 -Nt -Gint.grad
gmt makecpt -Cgeo -T-8000/5000 -D -Z  > 123.cpt
gmt grdimage -R$R -J$J Alaska.grd -C123.cpt -Iint.grad -Y8i -K > $PS
gmt pscoast -R$R -J$J -W0.5p,"#444444" -A$coast -Df -K -O >> $PS

# plot terrane
awk -F, '{print $11, $10}' $volcano | gmt psxy -R$R -J$J -St12p -W0.5p,black -Gred -K -O >> $PS
echo -161.894 55.417 | gmt psxy -R$R -J$J -St12p -W0.5p,black -Gmagenta1 -K -O >> $PS
echo -161.894 55.417 Pavlof | gmt pstext -J$J -R$R -F+a35+f9p -D0/0 -K -O >> $PS

gmt psxy -R$R -J$J -W1.5p,black -O -K << EOF >> $PS 
-163    55
-161    55.7
>
-161.5  54.5
-162.25 56.3 
EOF

gmt psbasemap -R$R -J$J -Bx1f1 -By1f1 -BWseN -K -O >> $PS 

plot_cross_section -163 55 -161 55.7 -161.894 55.417 50 $width 1.2 1.5 W e s A
plot_cross_section -161.5  54.5 -162.25 56.3 -161.894 55.417 50 $width 3.8 1.5 w E s B


R=-160.38/-158.38/55.17/57.17
J=m0.5i

## regional and station map
gmt grdcut @earth_relief_01m.grd -R$R -GAlaska.grd
gmt grdgradient Alaska.grd -A0 -Nt -Gint.grad
gmt makecpt -Cgeo -T-8000/5000 -D -Z  > 123.cpt
gmt grdimage -R$R -J$J Alaska.grd -C123.cpt -Iint.grad -Y-2.3i -X-5i -K -O >> $PS
gmt pscoast -R$R -J$J -W0.5p,"#444444" -A$coast -Df -K -O >> $PS

# plot terrane
awk -F, '{print $11, $10}' $volcano | gmt psxy -R$R -J$J -St12p -W0.5p,black -Gred -K -O >> $PS
echo -159.38 56.17 | gmt psxy -R$R -J$J -St12p -W0.5p,black -Gmagenta1 -K -O >> $PS
echo -159.38 56.17 Veniaminof | gmt pstext -J$J -R$R -F+a35+f9p -D0/0 -K -O >> $PS

gmt psxy -R$R -J$J -W1.5p,black -O -K << EOF >> $PS 
-160.5  55.75
-158.5  56.5  
>
-159    55.5
-159.9  57
EOF

gmt psbasemap -R$R -J$J -Bx1f1 -By1f1 -BWseN -K -O >> $PS 

plot_cross_section -160.5  55.75 -158.5  56.5 -159.38 56.17 50 $width 1.2 1.5 W e s A
plot_cross_section -159    55.5 -159.9  57 -159.38 56.17 50 $width 3.8 1.5 w E s B


R=-159.17/-157.17/55.88/57.88
J=m0.5i

## regional and station map
gmt grdcut @earth_relief_01m.grd -R$R -GAlaska.grd
gmt grdgradient Alaska.grd -A0 -Nt -Gint.grad
gmt makecpt -Cgeo -T-8000/5000 -D -Z  > 123.cpt
gmt grdimage -R$R -J$J Alaska.grd -C123.cpt -Iint.grad -Y-2.3i -X-5i -K  -O >> $PS
gmt pscoast -R$R -J$J -W0.5p,"#444444" -A$coast -Df -K -O >> $PS

# plot terrane
awk -F, '{print $11, $10}' $volcano | gmt psxy -R$R -J$J -St12p -W0.5p,black -Gred -K -O >> $PS
echo -158.17 56.88 | gmt psxy -R$R -J$J -St12p -W0.5p,black -Gmagenta1 -K -O >> $PS
echo -158.17 56.88 Aniakchak | gmt pstext -J$J -R$R -F+a35+f9p -D0/0 -K -O >> $PS

gmt psxy -R$R -J$J -W1.5p,black -O -K << EOF >> $PS 
-159.2  56.5
-157    57.25
>
-157.4  56
-159    57.9
EOF

gmt psbasemap -R$R -J$J -Bx1f1 -By1f1 -BWseN -K -O >> $PS 

plot_cross_section -159.2  56.5 -157    57.25 -158.17 56.88 50 $width 1.2 1.5 W e s A
plot_cross_section -157.4  56 -159    57.9 -158.17 56.88 50 $width 3.8 1.5 w E s B


R=-156.1/-154.1/57.236/59.236
J=m0.5i

## regional and station map
gmt grdcut @earth_relief_01m.grd -R$R -GAlaska.grd
gmt grdgradient Alaska.grd -A0 -Nt -Gint.grad
gmt makecpt -Cgeo -T-8000/5000 -D -Z  > 123.cpt
gmt grdimage -R$R -J$J Alaska.grd -C123.cpt -Iint.grad -Y-2.3i -X-5i -K -O >> $PS
gmt pscoast -R$R -J$J -W0.5p,"#444444" -A$coast -Df -K -O >> $PS

# plot terrane
awk -F, '{print $11, $10}' $volcano | gmt psxy -R$R -J$J -St12p -W0.5p,black -Gred -K -O >> $PS
echo -155.1 58.236 | gmt psxy -R$R -J$J -St12p -W0.5p,black -Gmagenta1 -K -O >> $PS
echo -155.1 58.236 Trident | gmt pstext -J$J -R$R -F+a35+f9p -D0/0 -K -O >> $PS

gmt psxy -R$R -J$J -W1.5p,black -O -K << EOF >> $PS 
-156    57.95  
-154    58.55
>
-154    57.4
-156    58.85
EOF

gmt psbasemap -R$R -J$J -Bx1f1 -By1f1 -BWSeN -K -O >> $PS 

plot_cross_section -156    57.95 -154    58.55 -155.1 58.236 50 $width 1.2 1.5 W e S A
plot_cross_section -154    57.4 -156    58.85 -155.1 58.236 50 $width 3.8 1.5 w E S B

gmt psscale -R$R -J$J -D2i/-0.5i+w3i/3p+h+e -Ctime.cpt -Ba2000f200+l"Time to 2024.1.1" -K -O >> $PS

gmt psconvert -A -Tf $PS
rm gmt.*
rm lined
rm *grad
rm staXY
rm topo.grd
rm tomolined.dat
rm $PS