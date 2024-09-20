#!/bin/bash
gmt --version
gmt gmtset MAP_FRAME_TYPE fancy
gmt gmtset MAP_FRAME_WIDTH 3p
gmt gmtset FONT_LABEL 10p, Times-Roman
gmt gmtset FONT_ANNOT_PRIMARY 10p,Times-Roman
gmt gmtset PS_MEDIA a3
gmt gmtset MAP_TITLE_OFFSET 1p
gmt gmtset MAP_LABEL_OFFSET 1p
gmt gmtset MAP_ANNOT_OFFSET 2p
gmt gmtset MAP_TICK_LENGTH_PRIMARY 2p
gmt gmtset MAP_TICK_LENGTH_SECONDARY 1p
gmt gmtset MAP_TICK_PEN_PRIMARY 1p
gmt gmtset MAP_TICK_PEN_SECONDARY 0.5p
gmt gmtset MAP_FRAME_PEN 1p
R=-162/-155/53/57
J=m0.4i
range=30
PS=figure3.ps

slipdir=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/rupturedatafile
seisf=/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all/catalog_bootstrap_40_1_associated.csv
numf=/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all/catalog_bootstrap_40_1_event_num.csv
cmtf=/mnt/home/jieyaqi/code/AlaskaEQ/data/cmt_sandpoint.csv
bdlst2=/mnt/ufs18/nodr/home/jieyaqi/alaska/4YJie/pb2002_steps.dat
coast=100
gmt makecpt -Cjet -T-99999999/99999999 -Iz -Z > cptfile.cpt
plot_cross_section() {
    depth="$5"
    staprojdis="$6"
    Xoff=$7
    Yoff=$8
    w=$9
    s=${10}
    start=${11}
    end=${12}
    text=${13}
    pfile=${14}
    echo $1 $2 $3 $4
    echo $start $end
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
    maxdist=`tail -n1 tomolined.dat | awk '{print $1}'`

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
        R1=-50/$maxdist/0/1
        R2=-50/$maxdist/0/$depth
        R3=-50/$maxdist/0/5
        x1_beach=`echo -50 + $trench | bc -l`
        x2_beach=`echo $maxdist + $trench | bc -l`
        R2_beach=$x1_beach/$x2_beach/0/$depth
    fi
    J1=x0.015i/0.3i
    J2=x0.015i/-0.015i
    J3=x0.015i/0.06i
    Y=`echo $depth \* 0.015 | bc -l`
    awk '{print $1, $4*0.001}' tomolined.dat | gmt psxy -R$R1 -J$J1 -W1p -X"$Xoff"i -Y"$Yoff"i -K -O -P >> $PS
    echo $pfile | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
    echo $pfile\' | gmt pstext -R$R1 -J$J1 -F+cTR+f10p -Dj0.03i/0i -K -O>> $PS
    gmt psbasemap -R$R1 -J$J1 -By1f0.5+l'Topo(km)' -B${w}se -K -O >> $PS

    awk '{print $1, $4*-0.001}' tomolined.dat | gmt psxy -R$R2 -J$J2 -W1p,darkgray -Gdarkgray -Y-"$Y"i -K -O >> $PS

    #seismicity
    /mnt/home/jieyaqi/anaconda3/envs/seis/bin/python3 staclose.py $seisf $1/$2/$3/$4 $staprojdis 1 2 $trench , > staXY

    # background
    awk -F, '$15<'$end' && $15>='$start' {print $1, $7, $28, $11}' staXY | gmt psxy -R -J -Sc0.1p -W#444444 -E+w0p+p0.6p,#444444 -K -O >> $PS
    # awk -F, '$15<'$end' && $15>='$start' {print $1, $7, $15, $28, $11}' staXY | gmt psxy -R -J -Sc1p -E+w0p+p0.1,#444444+cl -K -O >> $PS


    #slab
    gmt grdtrack lined -Gslab_Fan.grd -T0.1 | awk '{print $1, $2, $4}' > slab.grd
    python3 calculate_dist.py slab.grd 0 1 $1 $2 $trench > temp
    mv temp slab.grd
    awk '{print $1,$4}' slab.grd | gmt psxy -R$R2 -J -W1p,darkgray,- -K -O >> $PS

    echo $text | gmt pstext -R$R1 -J$J1 -F+cBL+f10p -Dj0.03i/0.03i -K -O>> $PS

    gmt psbasemap -R$R2 -J$J2 -By50f10 -Bx100f20 -B${w}${s}e -Bx+l'Distance(km)' -By+l'Depth(km)' -P -K -O >> $PS

    rm tomolined.dat
    rm lined
    rm slab.grd
    rm staXY
}

gmt grdcut @earth_relief_03m.grd -R$R -Gtopo.grd
depth=100
staprojdis=20
startlon=-159.2
startlat=54.5646
endlon=-160.2
endlat=54.5646
start=-99999999
end=0
pfile=A


gmt project -C$startlon/$startlat -E$endlon/$endlat -G0.025 > lined
trench=`python3 intersect.py lined trench.dat`
if [ -z $trench ]
then
    trench=0
fi

# topography
gmt grdtrack lined -Gtopo.grd | awk '{print $1, $2, $4}' > tomolined.dat
echo $startlon $startlat 0 > temp
awk 'NR==1{print '$startlon', '$startlat', $3}' tomolined.dat >> temp
cat tomolined.dat >> temp 
tail -n1 tomolined.dat | awk '{print '$endlon', '$endlat', $3}' >> temp
echo $endlon $endlat 0 >> temp
mv temp tomolined.dat
python3 calculate_dist.py tomolined.dat 0 1 $startlon $startlat $trench> temp
mv temp tomolined.dat
maxdist=`tail -n1 tomolined.dat | awk '{print $1}'`

if (( $(echo "$maxdist > 240" | bc -l) ))
then
    maxdist=240
fi

if [[ $trench == 0 ]]
then
    R1=0/$maxdist/0/1
    R2=0/$maxdist/0/$depth
    R3=0/$maxdist/0/5
else
    R1=-50/$maxdist/0/1
    R2=-50/$maxdist/0/$depth
    R3=-50/$maxdist/0/5
fi
J1=x0.015i/0.3i
J2=x0.015i/-0.015i
J3=x0.015i/0.06i
Y=`echo $depth \* 0.015 | bc -l`
awk '{print $1, $4*0.001}' tomolined.dat | gmt psxy -R$R1 -J$J1 -W1p -Y13i -K -P > $PS
echo $pfile | gmt pstext -R$R1 -J$J1 -F+cTL+f10p -Dj0.03i/0i -K -O>> $PS
echo $pfile\' | gmt pstext -R$R1 -J$J1 -F+cTR+f10p -Dj0.03i/0i -K -O>> $PS
gmt psbasemap -R$R1 -J$J1 -By1f0.5+l'Topo(km)' -BWse -K -O >> $PS

awk '{print $1, $4*-0.001}' tomolined.dat | gmt psxy -R$R2 -J$J2 -W1p,darkgray -Gdarkgray -Y-"$Y"i -K -O >> $PS

#seismicity
/mnt/home/jieyaqi/anaconda3/envs/seis/bin/python3 staclose.py $seisf $startlon/$startlat/$endlon/$endlat $staprojdis 1 2 $trench , > staXY

# background
awk -F, '$15<'$end' && $15>='$start' {print $1, $7, $28, $11}' staXY | gmt psxy -R -J -Sc0.1p -W#444444 -E+w0p+p0.6p,#444444 -K -O >> $PS

#slab
gmt grdtrack lined -Gslab_Fan.grd -T0.1 | awk '{print $1, $2, $4}' > slab.grd
python3 calculate_dist.py slab.grd 0 1 $startlon $startlat $trench > temp
mv temp slab.grd
awk '{print $1,$4}' slab.grd | gmt psxy -R$R2 -J -W1p,darkgray,- -K -O >> $PS

gmt psbasemap -R$R2 -J$J2 -By50f10 -Bx100f20 -BWse -Bx+l'Distance(km)' -By+l'Depth(km)' -P -K -O >> $PS

rm tomolined.dat
rm lined
rm slab.grd
rm staXY

plot_cross_section -159.6656 53.3 -159.6656 56 100 25 1.08 1.5 w s -999999999 0 "A) Seismicity earlier than Jun 2020" B
plot_cross_section -159.2 54.5646 -160.2 54.5646 100 25 -1.08 -0.4 W s 4428763.49 7742516.21 "" A
plot_cross_section -159.6656 53.3 -159.6656 56 100 25 1.08 1.5 w s 4428763.49 7742516.21 "B) Seismicity between Simeonof and Sand Point" B
plot_cross_section -159.2 54.5646 -160.2 54.5646 100 25 -1.08 -0.4 W S 7742516.21 999999999 "" A
plot_cross_section -159.6656 53.3 -159.6656 56 100 25 1.08 1.5 w S 7742516.21 999999999 "C) Seismicity after Sand Point" B

gmt psconvert -A -P -Tf $PS
rm gmt.*
rm topo.grd
rm $PS