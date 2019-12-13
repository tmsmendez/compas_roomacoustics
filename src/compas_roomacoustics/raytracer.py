import rhinoscriptsyntax as rs
import json

from compas.geometry import distance_point_point
from compas.geometry import vector_from_points


def shoot_rays(room):
    #TODO: energy has to be taken out according to absorption coefficient
    #TODO: ray loop should be a while loop, energy and time dependent
    #TODO: figure out a decent way to know which surface was hit
    #TODO: Check energy calculation, use different bs in some srfs
    reflectors = room.reflectors
    init_rays = room.source['init_rays']
    src = room.source['src_pt']
    ref = room.reflectors
    ref_srf = [ref[gk]['guid'] for gk in ref]

    rays = {}
    reflecting = reflectors
    for dk in init_rays:
        dir = init_rays[dk]['v']
        if 'src_pt' in init_rays[dk]:
            src_ = init_rays[dk]['src_pt']
        else:
            src_ = src
        w = room.source['init_rays'][dk]['power']
        rays[dk] = {'dir': dir, 'reflections':{}}
        for i in range(10): # this number should eventually be automated (while loop)
            ray = rs.ShootRay(reflecting, src_, dir, 2)
            srf = rs.PointClosestObject(ray[0], ref_srf)[0] # must be None in first ray!!!
            abs = ref[str(srf)]['abs_coeff']
            for wk in w: w[wk] *= (1 - abs[wk])
            l = distance_point_point(ray[0], ray[1])
            t = int((l / 343.0) * 1000)
            rays[dk]['reflections'][i] = {'time': t,
                                          'length': l,
                                          'power': w,
                                          'line': ((ray[0].X, ray[0].Y, ray[0].Z),
                                                   (ray[1].X, ray[1].Y, ray[1].Z))}
            dir = vector_from_points(ray[1], ray[2])
            src_ = ray[1]
    room.rays = rays

def rays_to_json(rays, filepath):
    with open(filepath, 'w+') as fp:
        json.dump(rays, fp)

def recs_to_json(recs, filepath):
    with open(filepath, 'w+') as fp:
        json.dump(recs, fp)

if __name__ == '__main__':
    import make_scene
    reload(make_scene)
    from make_scene import make_scene

    import plot_results
    reload(plot_results)
    from plot_results import visualize_rays


    for i in range(50): print ''
    if not rs.IsLayer('Scene'):
        rs.AddLayer('Scene', color=(50, 50, 255))
    rs.DeleteObjects(rs.ObjectsByLayer('Scene'))
    rs.DeleteObjects(rs.ObjectsByLayer('Default'))
    rs.CurrentLayer('Scene')

    source = {'type': 'fibonacci',
              'layer': 'source',
              'n': 10,
              'w': {'100':.1, '200':.1, '300':.1}}

    rec_dict = {'layer': 'recievers',
                'rec_r': .3}

    srf_layer = 'reflectors'
    room = make_scene(source, rec_dict, srf_layer)
    shoot_rays(room)
    visualize_rays(room.rays, ref_order=2)