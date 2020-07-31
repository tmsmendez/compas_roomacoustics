from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


__author__     = ['Tomas Mendez Echenagucia <tmendeze@uw.edu>']
__copyright__  = 'Copyright 2020, Design Machine Group - University of Washington'
__license__    = 'MIT License'
__email__      = 'tmendeze@uw.edu'

# import math, re, time, clr, os, json
# import Rhino, scriptcontext

import clr

clr.AddReference("Pachyderm_Acoustic")
clr.AddReference("Pachyderm_Acoustic_Universal")
clr.AddReference("Rhino_DotNet")
clr.AddReference("Hare")

from System import Array
import System.Collections.Generic.List as NetList
import Pachyderm_Acoustic as pach
import Pachyderm_Acoustic.Environment as env
import Pachyderm_Acoustic.Utilities.RC_PachTools as pt
import Pachyderm_Acoustic.Utilities.IR_Construction as ir
import Hare.Geometry.Point as hpt

from compas.utilities import geometric_key

from compas_roomacoustics.backends.pachyderm import assign_materials_by_layer
from compas_roomacoustics.backends.pachyderm import pach_sch_int
from compas_roomacoustics.backends.pachyderm import pach_edt
from compas_roomacoustics.backends.pachyderm import pach_t30
from compas_roomacoustics.backends.pachyderm import pach_sti
from compas_roomacoustics.backends.pachyderm import etcs_to_json
from compas_roomacoustics.backends.pachyderm import add_room_surfaces



def pach_run(src, mics, num_rays=1000, max_duration=2000, image_order=1):

    rec = NetList[hpt]()
    for mic in mics:
        rec.Add(hpt(mic[0], mic[1], mic[2]))

    src_h = hpt(src[0], src[1], src[2])
    octaves = Array[int]([0, 7])

    # - Acoustic Simulation ----------------------------------------------------
    # - 3d Scene ------
    scene = pt.Get_Poly_Scene(50, True, 20, 101.325, 0, True)

    PTList = NetList[hpt]()
    PTList.Add(src_h)

    for r in rec:
        PTList.Add(r)
    scene.partition(PTList, 10)
    env.RhCommon_PolygonScene.partition(scene, PTList, 10)

    # source power -------------------------------------------------------------
    swl = tuple([100.] * 8)
    Source = env.GeodesicSource(swl, src_h, 0)
    SourceIE = NetList[type(Source)]()
    SourceIE.Add(Source)
    receiver = pt.GetReceivers(rec, SourceIE, num_rays ,max_duration, 0, scene)

    # - Direct Sound Calculation -----------------------------------------------
    D = pach.Direct_Sound(Source, receiver[0], scene,octaves)
    Dout = pt.Run_Simulation(D)

    # - Source Image Calculation -----------------------------------------------
    IS = pach.ImageSourceData(Source,receiver[0], D, scene, image_order, 0)
    ISout = pt.Run_Simulation(IS)

    # - Ray Tracing  Calculation -----------------------------------------------
    RT = pach.SplitRayTracer(Source,
                             receiver[0],
                             scene,
                             max_duration,
                             octaves,
                             image_order,
                             num_rays)

    RTout = pt.Run_Simulation(RT)
    receiver_out = RTout.GetReceiver

    # - Energy Time Curves Calculation -----------------------------------------
    etcs = {}
    for i in range(len(mics)):
        gk = geometric_key(mics[i])
        etcs[gk] ={}
        for oct in range(8):
            etc =  ir.ETCurve(Dout, ISout, receiver_out, max_duration, 1000, oct, i, True)
            etcs[gk][oct] = etc
    return etcs

def room_to_pachyderm(room):
    add_room_surfaces(room)

if __name__ == '__main__':

    import os
    import rhinoscriptsyntax as rs
    
    from compas_roomacoustics.datastructures import Room

    path = 'c:\\users\\tmendeze\\documents\\uw_code\\compas_roomacoustics\\data'
    filename = 'simple_box.json'
    room = Room.from_json(os.path.join(path, filename))
    room_to_pachyderm(room)

    # rs.DeleteObjects(rs.ObjectsByLayer('Default'))
    
    # # user input ---------------------------------------------------------------
    # wall = {'abs': [17., 15., 10., 6., 4., 4., 5., 6.], 'sct': [.2] * 8, 'trn': [0] * 8}
    
    # lay_dict = {'walls': wall}
    
    # # run simulation -----------------------------------------------------------
    # src = rs.PointCoordinates(rs.ObjectsByLayer('src')[0])
    # mics = [rs.PointCoordinates(rpt) for rpt in rs.ObjectsByLayer('mics')]
    # assign_materials_by_layer(lay_dict)
    # etcs = pach_run(src, mics, num_rays=10000)

    # path = 'C:/Users/tmendeze/Documents/uw_code/compas_roomacoustics/temp/'
    # filepath = os.path.join(path, 'etcs.json')
    # etcs_to_json(filepath, etcs)
    # sch_int = pach_sch_int(etcs)
    # edt = pach_edt(sch_int)
    # t30 = pach_t30(sch_int)
    # sti = pach_sti(etcs)
    # names = ['edt', 't30', 'sti']
    
    # for i, index in enumerate([edt, t30, sti]):
    #     print(names[i])
    #     for j in index:
    #         print(index[j])
