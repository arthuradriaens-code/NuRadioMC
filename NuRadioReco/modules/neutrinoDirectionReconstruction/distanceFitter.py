from NuRadioReco.utilities import geometryUtilities as geo_utl
import scipy.optimize as opt
import numpy as np
from radiotools import helper as hp
from NuRadioReco.framework.parameters import stationParameters as stnp
from NuRadioMC.utilities import medium
from NuRadioMC.SignalProp import propagation
from NuRadioReco.framework.parameters import showerParameters as shp
import matplotlib.pyplot as plt
import pickle
import NuRadioReco.utilities.io_utilities


class distanceFitter:
    " Fits the direction using plane wave fit to channels "

    def __init__(self):



        pass


    def begin(self, det, lookup_table_path, channel_ids = [0, 3, 9, 10], template = None):
        self.__channel_ids = channel_ids
        self.__lookup_table_location = lookup_table_path
        self.__header = {}
        pass


    def run(self, evt, station, det, template = None, debug = True, debugplots_path = None):
        
        for channel in station.get_sim_station().iter_channels():
            if channel.get_id() == self.__channel_ids[0]:
                print("channel id", channel.get_id())
                shower_id = channel.get_shower_id()


        receive_pickle, launch_pickle, solution_pickle, zenith_vertex_pickle = pickle.load(open('/lustre/fs22/group/radio/plaisier/software/simulations/planeWaveFit/receive_launch.pkl', 'rb'))

        ice = medium.get_ice_model('greenland_simple')
        prop = propagation.get_propagation_module('analytic')



        self.__channel_pairs = []
        self.__relative_positions = []
        station_id = station.get_id()
        for i in range(len(self.__channel_ids) - 1):
            for j in range(i + 1, len(self.__channel_ids)):
                relative_positions = det.get_relative_position(station_id, self.__channel_ids[i]) - det.get_relative_position(station_id, self.__channel_ids[j])
                self.__relative_positions.append(relative_positions)

                self.__channel_pairs.append([self.__channel_ids[i], self.__channel_ids[j]])
        self.__lookup_table = {}
        for channel_id in self.__channel_ids:
            channel_z = abs(det.get_relative_position(station_id, channel_id)[2])
            if channel_z not in self.__lookup_table.keys():
                f = NuRadioReco.utilities.io_utilities.read_pickle('{}/lookup_table_{}.p'.format(self.__lookup_table_location, int(abs(channel_z))))
                self.__header[int(channel_z)] = f['header']
                self.__lookup_table[int(abs(channel_z))] = f['antenna_{}'.format(channel_z)]



        self.__sampling_rate = station.get_channel(0).get_sampling_rate()
        self.__template = template


        print("channel pairs", self.__channel_pairs)
        debug = True
        if debug:
            fig, axs = plt.subplots( len(self.__channel_pairs), 2, figsize = (10, len(self.__channel_pairs)*2))
        

        def likelihood(vertex, sim = False, rec = False, minimize = True):#, debug = False):#, station):
           # print("self.__correlation", self.__correlation)
            
            timings = np.zeros((len(self.__channel_ids), 2))
            solutiontype = np.zeros((len(self.__channel_ids), 2))
            for i_ch, channel_id in enumerate(self.__channel_ids):
                     #channel = station.get_channel(channel_id):
       
                    x2 = det.get_relative_position(station.get_id(), channel_id) + det.get_absolute_position(station.get_id())
                    r = prop( ice, 'GL1')
                    r.set_start_and_end_point(vertex, x2)

                    r.find_solutions()
                    for iS in range(r.get_number_of_solutions()):
                        timings[i_ch, iS] =r.get_travel_time(iS)# get_signal_travel_time(d_hor, z, ray_type, channel_id)#
                        solutiontype[i_ch, iS] = r.get_solution_type(iS)#if r.get_solution_type(iS) == self._raytypesolution:
                            
            corr = 0
            corrs = []
            aantal = 1
           
            for ich, ch_pair in enumerate(self.__channel_pairs):
#                print("ch_pair", ch_pair)
                index_1 = self.__channel_ids.index(ch_pair[0])
                index_2 = self.__channel_ids.index(ch_pair[1])
                #tmp1  = np.zeros(len(timings[index_1][np.array(timings[index_1] != 0)] * timings[index_2][np.array(timings[index_2] != 0)]))
                k = 0
                for t1, t2 in zip([0,0,1,1], [0,1,0,1]):#range(len(timings[index_1][np.array(timings[index_1] != 0)])), range(len(timings[index_2][np.array(timings[index_1] != 0)]))):
                    #### both solutiontypes are not the same as raytype trigger
                    #print("timings t1", timings[index_1, t1])
                    #print("timings t2", timings[index_2, t2])
                    #print("index 1", self.__channel_ids.index(ch_pair[0]))
                    #print("index 2", self.__channel_ids.index(ch_pair[1]))
                    #print('solution type 1', solutiontype[index_1, t1])
                    #print("solution type 2", solutiontype[index_2, t2])
                    if timings[index_1,t1]:
                        if timings[index_2,t2]:
                           
                            tmp = timings[index_2,t2 ] - timings[index_1, t1 ]## calculate timing

         
                            n_samples = tmp * self.__sampling_rate
             #   print("n_samples", n_samples)
             #   print("len corrleation", len(self.__correlation[ich]))
                            pos = int(len(self.__correlation[ich]) / 2 - n_samples)
                #print("pos", pos)
                #print('self.__correlation', self.__correlation[ich, pos])       
                           # print("pos", pos)
                #pos = len(self.__correlation[ich]) / 2 - n_samples
                            corr += self.__correlation[ich, pos]
                            corrs.append(self.__correlation[ich, pos])
                       #     aantal += 1
                            if sim:
                                #print("ich", ich)
                                #print("AX", ax)
                                if not k:
                                    axs[ ich, 0].plot(self.__correlation[ich])
                                 #   axs[ich, 0].axvline(pos, color = 'green', lw = 1, label = 'simulation')
                                    axs[ich, 0].axvline(pos, color = 'green', lw = 2, label = 'simulation')
                                    axs[ich, 0].axvline(int(len(self.__correlation[ich]) / 2), lw = 2, color = 'black', label = 'len(corr)/2')
                                    axs[ich, 0].legend()
                                    #axs[ich, 0].set_xlim((7000, 10000))
                    #ax[ich, 0].set_ylim((0, max(self.__correlation[ich])))
                #    print("self.__correlation[ich]", max(self.__correlation[0]))
                                axs[ich, 0].axvline(pos, color = 'green', lw = 2)#self.__correlation[ich, pos])
                                #axs[ich,0].legend()
                            if rec:
               #     print("ax shape", self.__correlation[ich, pos])
    #                            axs[ ich, 0].plot(self.__correlation[ich])
                                axs[ich, 0].set_ylim((0, max(self.__correlation[ich])))
                 #   print("self.__correlation[ich]", max(self.__correlation[0]))
     
                                axs[ich, 0].axvline(pos, color = 'red', lw = 2)#self.__correlation[ich, pos])
     
                                if not k:#ich == 0:
                                    axs[ich, 1].plot(station.get_channel(ch_pair[0]).get_times(), station.get_channel(ch_pair[0]).get_trace())
                  #  print("plot cannels", ch_pair)
                                    axs[ich, 1].plot(station.get_channel(ch_pair[1]).get_times(), station.get_channel(ch_pair[1]).get_trace())
                                    axs[ich, 0].axvline(pos, color = 'red', lw = 2, label = 'reconstruction')
                                    #axs[ich,1].set_xlim((1600, 2100))
                                    axs[ich, 0].legend()
                                    axs[ich, 0].grid()
                            k += 1
            if rec:         
                 fig.tight_layout()
                 fig.savefig("{}/corr_vertex.pdf".format(debugplots_path))




            likelihood = corr
            if not minimize:
                return corrs
            return -1*likelihood





        trace = np.copy(station.get_channel(self.__channel_pairs[0][0]).get_trace())
        self.__correlation = np.zeros((len(self.__channel_pairs), len(hp.get_normalized_xcorr(trace, self.__template))) )
        for ich, ch_pair in enumerate(self.__channel_pairs):
            #print("self.__channel_pairs[0]", self.__channel_pairs[ich][0])                
            trace1 = np.copy(station.get_channel(self.__channel_pairs[ich][0]).get_trace())
            #print("channel", station.get_channel(4).get_trace())
            trace2 =np.copy(station.get_channel(self.__channel_pairs[ich][1]).get_trace())
 
            #print("times trace 1", np.copy(station.get_channel(self.__channel_pairs[ich][0]).get_times()))
            #print("times trace2", np.copy(station.get_channel(self.__channel_pairs[ich][1]).get_times()))
            #print(stop)
            corr_1 = hp.get_normalized_xcorr(trace1, self.__template)
            #print("corr 1", corr_1)
            corr_2 = hp.get_normalized_xcorr(trace2, self.__template)
           
          
            #print("len corr1", len(corr_1))
           # print("corr 2", corr_2)
            #print(stop)
            #print("len channel pairs", len(self.__channel_pairs))
           # self.__correlation = np.zeros((len(self.__channel_pairs), len(corr_1)))
            sample_shifts = np.arange(-len(corr_1) // 2, len(corr_1) // 2, dtype=int)
            toffset = sample_shifts / station.get_channel(0).get_sampling_rate()
            for i_shift, shift_sample in enumerate(sample_shifts):
              #  print("corr 2", corr_2)
                if (np.isnan(corr_2).any()):# or (not corr_2): ### with noise this should not be needed
                    self.__correlation[ich, i_shift] = 0#np.zeros(len(corr_2))
                #    print("self correlation",np.zeros(len(corr_2)))
                elif (np.isnan(corr_1).any()):
                    self.__correlation[ich, i_shift] = 0#np.zeros(len(corr_2))

                else:
                    self.__correlation[ich, i_shift] = np.max(corr_1 * np.roll(corr_2, shift_sample)) 

        #print("stop", stop)



        #### get receive zenith from planewave
        receive_zenith = station[stnp.nu_zenith]
	#### translate receive zenith to launch vector
        #receive_zenith = np.deg2rad(78.9695)
        zenith_vertex = zenith_vertex_pickle[np.argmin(abs(np.rad2deg(receive_pickle) - np.rad2deg(receive_zenith)))] ## deze aanpassen aan diepte #full distance inladen. 
        
        print("simulated corrs", likelihood(evt.get_sim_shower(shower_id)[shp.vertex], minimize = False))
        print("##################################")#





##################################")


        print("len simulated corrs", len(likelihood(evt.get_sim_shower(shower_id)[shp.vertex], minimize = False)))
        print("simulated value", likelihood(evt.get_sim_shower(shower_id)[shp.vertex], sim = True))
        print("simulated vertex", evt.get_sim_shower(shower_id)[shp.vertex])
        print("reconstructed azimuth", np.rad2deg(station[stnp.nu_azimuth]))
        print("vertex azimuht simulated", np.rad2deg(hp.cartesian_to_spherical(*evt.get_sim_shower(shower_id)[shp.vertex])[1]))
        print("vertex zenith simulared", np.rad2deg(hp.cartesian_to_spherical(*evt.get_sim_shower(shower_id)[shp.vertex])[0]))
        #print("azimuth simulated", np.rad2deg(hp.cartesian_to_spherical(*evt.get_sim_shower(shower_id)[shp.vertex])[1]))
       
        

        print("zenith vertex from pickle", zenith_vertex)
      
#        print(stop) 
        range_vertices = []
        depths =np.arange(500, 700, 20)#[680]#np.arange(100,2500, 10)# range(100, 1000, 10)
        for depth in depths:#range(200, 400, 10): ## change such that it check 10 degrees for first 1000 
            diff_tmp = np.inf
            if depth > 390:
                delta = .2
                diff = 4
                diff_az = 2
            else: 
                diff = 10
                delta = .2
        #    zenith_vertex = np.rad2deg(hp.cartesian_to_spherical(*evt.get_sim_shower(shower_id)[shp.vertex])[0])
            for zen in np.arange(zenith_vertex -diff, zenith_vertex + diff, delta):
                azimuth_tmp = station[stnp.nu_azimuth]#hp.cartesian_to_spherical(*evt.get_sim_shower(shower_id)[shp.vertex])[1]#station[stnp.nu_azimuth]
                for az in np.arange(np.rad2deg(azimuth_tmp) - diff, np.rad2deg(azimuth_tmp) + diff, delta):
                    if 0:
                        cart_tmp = hp.spherical_to_cartesian(np.deg2rad(zen), np.deg2rad(az))
                #depth = -1*depth
                #print("vertex tmp", cart_tmp)
                #print(stop)
                        R_tmp = -1*depth/ cart_tmp[2]
                        x1_tmp = cart_tmp * R_tmp
                        #       print('x1', x1_tmp)


                        x1_tmp = [x1_tmp[0],x1_tmp[1],x1_tmp[2]]
                        x2 = [0,0,-97]
        #        print("zenith vertex sim", np.rad2deg(hp.cartesian_to_spherical(*evt.get_sim_shower(shower_id)[shp.vertex])[0]))
        #        print("x1_tmp", x1_tmp)
        #        print("zenith vertex tmp", np.rad2deg(hp.cartesian_to_spherical(*x1_tmp)[0]))
        #        print("azimuth vertex tmp", np.rad2deg(hp.cartesian_to_spherical(*x1_tmp)[1]))
        #        print("zenih vertex from rec", zenith_vertex)
        #        print("azimuth rec", np.rad2deg(station[stnp.nu_azimuth]))
                        ice = medium.get_ice_model('greenland_simple')
                        prop = propagation.get_propagation_module('analytic')
                        r = prop( ice, 'GL1')
                        r.set_start_and_end_point(x1_tmp, x2)
            #    print("x1_tmp", x1_tmp)
                        r.find_solutions()
                        if(not r.has_solution()):
        #            print("warning: no solutions")
                            continue

                        else:
                            for iS in range(r.get_number_of_solutions()):
                                if abs(np.rad2deg(hp.cartesian_to_spherical(*r.get_receive_vector(iS))[0]) - np.rad2deg(receive_zenith)) < diff_tmp:
                                    diff_tmp = abs(np.rad2deg(hp.cartesian_to_spherical(*r.get_receive_vector(iS))[0]) - np.rad2deg(receive_zenith))
                    #        print("Diff tmp", diff_tmp)
                                    zen_tmp = zen
                   # print("depth", depth)
        #            print("vertex", x1_tmp)
          
                
                    cart = hp.spherical_to_cartesian(np.deg2rad(zen), np.deg2rad(az))
                    R = -1*depth/cart[2]
                    x1 = cart * R
                    if (np.sqrt(x1[0]**2 + x1[1]**2 + x1[2]**2) < 4000):
                    #R = -1*depth/ cart[2]
                    #x1 = cart * R 
        #                print("Used vertex", x1)
        #                print("azimuth used vertex", np.rad2deg(hp.cartesian_to_spherical(*x1)[1]))
                        range_vertices.append(x1)


        #print("range of vertices for reco:", range_vertices)
        print("simulated vertex:", evt.get_sim_shower(shower_id)[shp.vertex])
        print("try", np.array(range_vertices)[:,2])
        #print(stop)
 	#### get for a series of depth the vertex position that corresopnds to receive zenith
        if debug:
            likelihood_values = []
            for vertex in range_vertices:
             #   print("reconstruction for vertex", vertex)
                likelihood_values.append(likelihood(vertex))
     
            fig1 =  plt.figure()
            ax1 = fig1.add_subplot(111)
            ax1.plot(np.array(range_vertices)[:,2], likelihood_values, 'o', markersize = 3, color = 'blue')
            #ax1.plot(np.array(range_vertices)[:,2], likelihood_values, color = 'blue')
            ax1.set_xlabel("vertex z [m]")
            ax1.set_ylabel("minimization value")
            ax1.axvline(evt.get_sim_shower(shower_id)[shp.vertex][2], label = 'simulated', color = 'green')
            ax1.axvline(range_vertices[np.argmin(likelihood_values)][2], label = 'reconstructed depth', color = 'red')
            ax1.axhline(likelihood(evt.get_sim_shower(shower_id)[shp.vertex], sim = True), color = 'green')
            ax1.legend()
            fig1.savefig("{}/vertex_likelihood.pdf".format(debugplots_path))
        #print("simulated vertex", likelihood(evt.get_sim_shower(shower_id)[shp.vertex], sim = True))
        if 0:#debug:
            fig1 =  plt.figure()
            ax1 = fig1.add_subplot(111)
            ax1.plot(np.array(range_vertices)[:,2], likelihood_values, 'o', markersize = 3, color = 'blue')
            
            ax1.pcolor(xx, yy, zz)#ax1.plot(np.array(range_vertices)[:,2], likelihood_values, color = 'blue')
            ax1.set_xlabel("vertex z [m]")
            ax1.set_ylabel("minimization value")
            ax1.axvline(evt.get_sim_shower(shower_id)[shp.vertex][2], label = 'simulated', color = 'green')
            ax1.axvline(range_vertices[np.argmin(likelihood_values)][2], label = 'reconstructed depth', color = 'red')
            ax1.axhline(likelihood(evt.get_sim_shower(shower_id)[shp.vertex], sim = True), color = 'green')
            ax1.legend()
            fig1.savefig("{}/vertex_map.pdf".format(debugplots))



        station[stnp.nu_vertex] = range_vertices[np.argmin(likelihood_values)]
        print("reconstructed vertex", station[stnp.nu_vertex])
        print("simulated corrs", likelihood(evt.get_sim_shower(shower_id)[shp.vertex], minimize = False))
        print("len simulated corrs", len(likelihood(evt.get_sim_shower(shower_id)[shp.vertex], minimize = False)))
        print("simulated value", likelihood(evt.get_sim_shower(shower_id)[shp.vertex], sim = True))   
        print("reconstructed value", likelihood(station[stnp.nu_vertex], rec = True))
        print("reconstructed corrs", likelihood(station[stnp.nu_vertex], minimize = False))
        print("len reconstructed corrs", len(likelihood(station[stnp.nu_vertex], minimize = False)))
        print("simulated vertex", evt.get_sim_shower(shower_id)[shp.vertex])
        ### for each vertex position calculate the likelihood
        
        
        
        
        def get_signal_travel_time(self, d_hor, z, ray_type, channel_id):
            """
            Calculate the signal travel time between a position and the
            channel
            Parameters:
            ------------
            d_hor, z: numbers or arrays of numbers
                Coordinates of the point from which to calculate the
                signal travel times. Correspond to (r, z) coordinates
                in cylindrical coordinates.
            ray_type: string
                Ray type for which to calculate the travel times. Options
                are direct, reflected and refracted
            channel_id: int
                ID of the channel to which the travel time shall be calculated
            """
            channel_pos = self.__detector.get_relative_position(self.__station_id, channel_id)
            channel_type = int(abs(channel_pos[2]))
            travel_times = np.zeros_like(d_hor)
            mask = np.ones_like(travel_times).astype(bool)
            i_z = np.array(np.round((z - self.__header[channel_type]['z_min']) / self.__header[channel_type]['d_z'])).astype(int)
            i_x_1 = np.array(np.floor((d_hor - self.__header[channel_type]['x_min']) / self.__header[channel_type]['d_x'])).astype(int)
            cell_dist_1 = i_x_1 * self.__header[channel_type]['d_x'] + self.__header[channel_type]['x_min']
            mask[i_x_1 > self.__lookup_table[channel_type][ray_type].shape[0] - 1] = False
            mask[i_z > self.__lookup_table[channel_type][ray_type].shape[1] - 1] = False
            i_x_1[~mask] = 0
            i_z[~mask] = 0
            travel_times_1 = self.__lookup_table[channel_type][ray_type][(i_x_1, i_z)]
            i_x_2 = np.array(np.ceil((d_hor - self.__header[channel_type]['x_min']) / self.__header[channel_type]['d_x'])).astype(int)
            cell_dist_2 = i_x_2 * self.__header[channel_type]['d_x'] + self.__header[channel_type]['x_min']
            i_x_2[~mask] = 0
            travel_times_2 = self.__lookup_table[channel_type][ray_type][(i_x_2, i_z)]
            slopes = np.zeros_like(travel_times_1)
            slopes[i_x_2 > i_x_1] = (travel_times_1 - travel_times_2)[i_x_2 > i_x_1] / (cell_dist_1 - cell_dist_2)[i_x_2 > i_x_1]
            travel_times = (d_hor - cell_dist_1) * slopes + travel_times_1
            travel_times[~mask] = np.nan
            return travel_times
            
            
        
        
        
    def end(self):
            pass


