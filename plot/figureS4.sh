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
R=-162/-155/53/57
J=m0.4i
range=30
PS=figureS4.ps

profp=/mnt/home/jieyaqi/code/AlaskaEQ/data/Shillington_active
slipdir=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/rupturedatafile
seisf=/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/iter2/catalogs_bootstrap_processed_associated_new.csv
rupturedir=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/AKruptures
terrane=../data/Alaska_terrane.dat
cmtf=../data/cmt.csv
bdlst2=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/pb2002_steps.dat
coast=100

plot_cross_section() {
    depth="$5"
    staprojdis="$6"
    range="$7"
    Xoff=$8
    Yoff=$9
    w=${10}
    e=${11}
    s=${12}
    text=${13}
    echo $1 $2 $3 $4
    gmt project -C$1/$2 -E$3/$4 -G0.025 > lined
    trench=`python3 intersect.py lined trench.dat`
    if [ -z $trench ]
    then
        trench=0
    fi

    # topography
    gmt grdtrack lined -Gtopo.grd | awk '{print $1, $2, $4}' > tomolined.dat
    echo $1 $2 0 > temp
    awk 'NR==1{print '$1', '$2', $3}' tomolined.dat >> temp
    cat tomolined.dat >> temp 
    tail -n1 tomolined.dat | awk '{print '$3', '$4', $3}' >> temp
    echo $3 $4 0 >> temp
    mv temp tomolined.dat
    python3 calculate_dist.py tomolined.dat 0 1 $1 $2 $trench> temp
    mv temp tomolined.dat
    mindist=`head -n1 tomolined.dat | awk '{print $1}'`
    maxdist=`tail -n1 tomolined.dat | awk '{print $1}'`

    # slip
    gmt grdtrack lined -G$slipdir/simeonof_slip.grd | awk '{print $1, $2, $4}' > temp
    python3 calculate_dist.py temp 0 1 $1 $2 $trench > simeonof_slip
    gmt grdtrack lined -G$slipdir/chignik_slip.grd | awk '{print $1, $2, $4}' > temp
    python3 calculate_dist.py temp 0 1 $1 $2 $trench > chignik_slip
    if (( $(echo "$mindist < -240" | bc -l) ))
    then
        mindist=-240
    fi
    if (( $(echo "$maxdist > 240" | bc -l) ))
    then
        maxdist=240
    fi

    if [[ $trench == 0 ]]
    then
        R1=0/$maxdist/0/1
        R2=0/$maxdist/0/$depth
        R3=0/$maxdist/0/5
        R2_beach=$R2
    else
        R1=-180/20/0/1
        R2=-180/20/0/$depth
        R3=-180/20/0/5
        x1_beach=`echo -180 + $trench | bc -l`
        x2_beach=`echo 20 + $trench | bc -l`
        R2_beach=$x1_beach/$x2_beach/0/$depth
    fi
    J1=x0.02i/0.3i
    J2=x0.02i/-0.02i
    J3=x0.02i/0.06i
    Y=`echo $depth \* 0.02 | bc -l`
    awk '{print $1, $4*0.001}' tomolined.dat | gmt psxy -R$R1 -J$J1 -W1p -X"$Xoff"i -Y"$Yoff"i -K -O -P >> $PS
    # plot location of A-A'
    if [[ ${14} == 1 ]]
    then
        # A-A' 159.609377605-243.98422167861142
        echo -84.3748440736 0.2 | gmt psxy -R$R1 -J$J1 -Si7p -Gblack -K -O >> $PS
    fi

    gmt psbasemap -R$R1 -J$J1 -By1f0.5+l'Topo(km)' -B${w}s -K -O >> $PS
    awk '{print $1, $4}' simeonof_slip | gmt psxy -R$R3 -J$J3 -W1p,"#E02514" -K -O >> $PS
    awk '{print $1, $4}' chignik_slip | gmt psxy -R$R3 -J$J3 -W1p,"#40A362" -K -O >> $PS
    echo $text | gmt pstext -R$R1 -J$J1 -F+cTL+f13p -Dj0.03i/0i -K -O>> $PS
    echo $text\' | gmt pstext -R$R1 -J$J1 -F+cTR+f13p -Dj0.03i/0i -K -O>> $PS
    gmt psbasemap -R$R3 -J$J3 -By5f1+l'Slip(m)' -Bs$e -K -O >> $PS

    awk '{print $1, $4*-0.001}' tomolined.dat | gmt psxy -R$R2 -J$J2 -W1p,darkgray -Gdarkgray -Y-"$Y"i -K -O >> $PS

    #seismicity
    /mnt/home/jieyaqi/anaconda3/envs/seis/bin/python3 staclose.py $seisf $1/$2/$3/$4 $staprojdis 1 2 $trench , > staXY

    # Sandpoint
    awk -F, '$20 && $20>=0 && $20<='$range' {print $1, $7, $20, $11, $12}' staXY | gmt psxy -R$R2 -J$J2 -Sc1p -Csandpoint.cpt -E+w0p+p0.6+cl -K -O >> $PS

    # Simeonof
    awk -F, '$19 && $19>=0 && $19<='$range' {print $1, $7, $19, $11, $12}' staXY | gmt psxy -R$R2 -J$J2 -Sc1p -Csimeonof.cpt -E+w0p+p0.6+cl -K -O >> $PS

    # Chiknik
    awk -F, '$21 && $21>=0 && $21<='$range' {print $1, $7, $21, $11, $12}' staXY | gmt psxy -R$R2 -J$J2 -Sc1p -Cchignik.cpt -E+w0p+p0.6+cl -K -O >> $PS

    # CMT
    ## Sand Point
    # awk -F, '$22 && $20 && $20<0 {print $5, $6, $7, $22, $23, $24, $25, $26, $27, $28, $1, $7, $20}' staXY |\
    # gmt pscoupe -J$J2 -R$R2_beach -Aa$1/$2/$3/$4/90/10000/0/$depth -Sm10p -Q -G#444444 -K -O >> $PS 
    awk -F, '$22 && $20>=0 && $20<='$range' {print $5, $6, $7, $22, $23, $24, $25, $26, $27, $28, $1, $7, $20}' staXY |\
    while read line
    do
        value=`echo $line | awk '{print $13}'`
        color=`python3 get_color.py $value sandpoint.cpt` 
        echo $line | awk '{print $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12}'| gmt pscoupe -J$J2 -R$R2_beach -Aa$1/$2/$3/$4/90/10000/0/$depth -Sm11p -Q -G$color -K -O >> $PS 
    done

    awk -F, '$22 && $19>=0 && $19<='$range' {print $5, $6, $7, $22, $23, $24, $25, $26, $27, $28, $1, $7, $19}' staXY |\
    while read line
    do
        value=`echo $line | awk '{print $13}'`
        color=`python3 get_color.py $value simeonof.cpt` 
        echo $line | awk '{print $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12}'| gmt pscoupe -J$J2 -R$R2_beach -Aa$1/$2/$3/$4/90/10000/0/$depth -Sm11p -Q -G$color -K -O >> $PS 
    done

    awk -F, '$22 && $21>=0 && $21<='$range' {print $5, $6, $7, $22, $23, $24, $25, $26, $27, $28, $1, $7, $21}' staXY |\
    while read line
    do
        value=`echo $line | awk '{print $13}'`
        color=`python3 get_color.py $value chignik.cpt` 
        echo $line | awk '{print $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12}'| gmt pscoupe -J$J2 -R$R2_beach -Aa$1/$2/$3/$4/90/10000/0/$depth -Sm11p -Q -G$color -K -O >> $PS 
    done
    # background
    awk -F, '$18<0 {print $1, $7, $18}' staXY | gmt psxy -R$R2 -J$J2 -Sc3p -G"#444444" -t20 -K -O >> $PS
    
    #slab
    gmt grdtrack lined -Gslab_Fan.grd -T0.1 | awk '{print $1, $2, $4}' > slab.grd
    python3 calculate_dist.py slab.grd 0 1 $1 $2 $trench > temp
    mv temp slab.grd
    awk '{print $1,$4}' slab.grd | gmt psxy -R$R2 -J -W1.5p,#999999 -K -O >> $PS
    gmt psbasemap -R$R2 -J$J2 -By50f10 -Bx100f20 -B${w}${s}e -Bx+l'Distance(km)' -By+l'Depth(km)' -P -K -O >> $PS

    # rm tomolined.dat
    # rm lined
    # rm slab.grd
    # rm staXY
    # rm simeonof_slip
    # rm chignik_slip

}

gmt grdcut @earth_relief_03m.grd -R$R -Gtopo.grd
gmt pscoast -R$R -J$J -W0.5p,darkgray -Swhite -A$coast -Df -K -Y13i -P > $PS
grep NA\/PA $bdlst2 | awk '{print $3,$4}' | gmt psxy -J -R -W1.5 -O -K >> $PS
gmt grdcontour $slipdir/simeonof_slip.grd -C+0.5,1,1.5 -J$J -R$R -W1,black -O -K >> $PS
gmt grdcontour $slipdir/chignik_slip.grd -C+0.5,1,1.5 -J$J -R$R -W1,black -O -K >> $PS 

awk -F, 'NR>1&&$15<0{print $2, $3, $15}' $seisf | gmt psxy -R$R -J$J -Sc1p -G"#444444" -K -O >> $PS

# plot terrane
# gmt psxy -R -J$J  $terrane -W1,black -O -K  >> $PS

## rupture zones
gmt psxy -R -J$J  $rupturedir/1946davies.lin -W1,black,- -: -h4 -O -K  >> $PS
gmt psxy -R -J$J  $rupturedir/1948davies.lin -W1,black,- -: -h4 -O -K  >> $PS
gmt psxy -R -J$J  $rupturedir/1957davies.lin -W1,black,- -: -h4 -O -K  >> $PS
gmt psxy -R -J$J  $rupturedir/1964davies.lin -W1,black,- -: -h4 -O -K  >> $PS
gmt psxy -R -J$J  $slipdir/far_eastern_1m.gmtlin -W1,black,- -h4 -O -K  >> $PS

# Simeonof
gmt makecpt -C"#E02514","#FFB347" -T0,$range -Z > simeonof.cpt
awk -F, '$16>=0 && $16<='$range' && NR>1 {print $2, $3, $16}' $seisf | gmt psxy -R$R -J$J -Sc3p -W0.5p+cl -Csimeonof.cpt -K -O >> $PS
awk -F, '$14 && $14>=0 && $14<='$range' && NR>1{print $1, $2, $14, $4, $5, $6, $7, $8, $9, $10, $1, $2 }' $cmtf| gmt psmeca -J$J -R$R -Sm5p -Zsimeonof.cpt -K -O >> $PS
echo -159.28 54.83 36 4.15 -3.23 -0.92 5.38 2.93 -1.65 27 X Y | gmt psmeca -J$J -R$R -Sm5p -Gred -K -O >> $PS

# gmt psscale -Csimeonof.cpt -D3.3i/2.3i+w1.7i/3p+h+e -Bx+l'Days after Simeonof' -O -K>> $PS

# Sandpoint
gmt makecpt -C"#4E00F5","#67B9E0" -T0,$range -Z > sandpoint.cpt
awk -F, '$17>=0 && $17<='$range' && NR>1 {print $2, $3, $17}' $seisf | gmt psxy -R$R -J$J -Sc3p -W0.5p+cl -Csandpoint.cpt -K -O >> $PS
awk -F, '$15 && $15>=0 && $15<='$range' && NR>1{print $1, $2, $15, $4, $5, $6, $7, $8, $9, $10, $1, $2 }' $cmtf| gmt psmeca -J$J -R$R -Sm5p -Zsandpoint.cpt -K -O >> $PS
echo -159.70 54.48 37 0.05 -0.52 0.46 1.87 0.70 2.15 27 X Y | gmt psmeca -J$J -R$R -Sm5p -Gblue -K -O >> $PS

# gmt psscale -Csandpoint.cpt -D5.2i/2.3i+w1.7i/3p+h+e -Bx+l'Days after Sand-point' -O -K>> $PS

# Chiknik
gmt makecpt -C"#40A362","#9EA980" -T0,$range -Z > chignik.cpt
awk -F, '$18>=0 && $18<='$range' && NR>1 {print $2, $3, $18}' $seisf | gmt psxy -R$R -J$J -Sc3p  -W0.5p+cl -Cchignik.cpt -K -O >> $PS
awk -F, '$16 && $16>=0 && $16<='$range' && NR>1{print $1, $2, $16, $4, $5, $6, $7, $8, $9, $10, $1, $2 }' $cmtf| gmt psmeca -J$J -R$R -Sm5p -Zchignik.cpt -K -O >> $PS
echo -157.32 55.40 30 1.03 -0.77 -0.26 2.39 1.37 -0.48 28 X Y | gmt psmeca -J$J -R$R -Sm5p -Ggreen -K -O >> $PS

# gmt psscale -Cchignik.cpt -D7.1i/2.3i+w1.7i/3p+h+e -Bx+l'Days after Chiknik' -O -K>> $PS

gmt pslegend -R$R -J$J -DJTR+o0.5i/-0.75i+w1.7i -O -K >> $PS << EOF
S -0.04i - 0.25i - 1p,#999999 10p slab
G 0.05i
S -0.04i - 0.25i - 1p,#40A362 10p slip contour of Chignik
G 0.1i
B simeonof.cpt 0i 3p+h+e -Bx30f5+l"Days after Simeonof"
EOF

gmt pslegend -R$R -J$J -DJTR+o2.4i/-0.75i+w1.7i -O -K >> $PS << EOF
S -0.04i - 0.25i - 1p 10p topography
G 0.05i
S -0.04i - 0.25i - 1p,#E02514 10p slip contour of Simeonof
G 0.1i
B sandpoint.cpt 0i 3p+h+e -Bx30f5+l"Days after Sand Point"
EOF

gmt pslegend -R$R -J$J -DJTR+o4.3i/-0.75i+w1.7i -O -K >> $PS << EOF
S -0.04i c 2.5p #444444 - 10p seismicity before June 2020
G 0.05i
S -0.04i e 8p darkgray - 10p water shade
G 0.1i
B chignik.cpt 0i 3p+h+e -Bx30f5+l"Days after Chignik"
EOF

awk '{print $5, $4}' $profp/MGL1110_MCS03.shotlog | gmt psxy -R$R -J$J -W1.5p,black -O -K  >> $PS
awk '{print $5, $4}' $profp/MGL1110_MCS04.shotlog | gmt psxy -R$R -J$J -W1.5p,black -O -K  >> $PS
awk '{print $5, $4}' $profp/MGL1110_MCS05B.shotlog | gmt psxy -R$R -J$J -W1.5p,black -O -K  >> $PS

gmt psxy -R$R -J$J -W1.5p,black -O -K << EOF >> $PS 
-155.488710   53.655269
-158.007885 56.298382
>
-157.630011  52.915365
-159.221448  55.646599
>
-159.528878  52.599848
-160.758048	   55.096458
EOF

gmt pstext -R$R -J$J -F+f13p,bold -D-0.01i/0.1i -K -O << EOF >> $PS
-158.007885 56.298382 3
-159.221448  55.646599 4
-160.758048	   55.096458 5	
EOF



gmt psbasemap -R$R -J$J -Bx5f1 -By2f1 -BWseN -K -O >> $PS 

plot_cross_section -158.007885 56.298382 -155.488710   53.655269 100 25 $range 3.3 1.5 W E s 3 0
plot_cross_section -159.221448  55.646599 -157.630011  52.915365 100 25 $range 0 -0.4 W E s 4 0
plot_cross_section -160.758048	   55.096458 -159.528878  52.599848 100 25 $range 0 -0.4 W E S 5 0
# plot_cross_section -160.5 56.05 -159.1 53.40 100 25 $range 4.45 1.5  w E s D 0
# plot_cross_section -159.72 56.13 -158.15 53.55 100 25 $range -4.45 -0.4 W e s E 0
# plot_cross_section -158.95 56.3 -157.2 53.75 100 25 $range 4.45 1.5 w E s F 0
# plot_cross_section -158.1 56.5 -156.2 53.9 100 25 $range -4.45 -0.4 W e S G 0
# plot_cross_section -157.5 56.75 -155.25 54.15 100 25 $range 4.45 1.5 w E S H 0






# N=`awk 'END {print NR}' $1`
# i=1
# while [ "$i" -le "$N" ]
# do
#     start=`awk 'NR=='$i' {print $0}' $1`
#     end=`awk 'NR=='$((i+1))' {print $0}' $1`
#     echo $start $end
#     bash plot_profile_aftershock.sh $start $end 100 25 $range aftershock
#     # sh plot_background_1819.sh $start $end 100 25 aftershock
#     i=$(( i + 3 ))
# done

gmt psconvert -A -P -Tf $PS
rm gmt.*
rm topo.grd
rm $PS