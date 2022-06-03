import numpy as np
import copy
import copy
import sly_globals as g


# 99.9 percentile of the l2 velocity error distribution (per clss / 0.5 second)
# This is an earlier statistcs and I didn't spend much time tuning it.
# Tune this for your model should provide some considerable AMOTA improvement
CLS_VELOCITY_ERROR = {
    'car':4,
    'truck':4,
    'bus':5.5,
    'trailer':3,
    'pedestrian':1,
    'motorcycle':13,
    'bicycle':3,
    'construction_vehicle':0,
    'barrier':0,
    'traffic_cone':0
}



class PubTracker(object):
    def __init__(self, max_age=0):
        self.hungarian = False
        self.max_age = max_age

        self.CLS_VELOCITY_ERROR = CLS_VELOCITY_ERROR

        self.reset()
    
    def greedy_assignment(self, dist):
        matched_indices = []
        if dist.shape[1] == 0:
            return np.array(matched_indices, np.int32).reshape(-1, 2)
        for i in range(dist.shape[0]):
            j = dist[i].argmin()
            if dist[i][j] < 1e16:
                dist[:, j] = 1e18
                matched_indices.append([i, j])
        return np.array(matched_indices, np.int32).reshape(-1, 2)

    def reset(self):
        self.id_count = 0
        self.tracks = []

    def step_centertrack(self, results, time_lag):
        if len(results) == 0:
            self.tracks = []
            return []
        else:
            temp = []
            for det in results:
                # filter out classes not evaluated for tracking 
                if det['detection_name'] not in g.gt_labels.keys():
                    continue 

                det['ct'] = np.array(det['translation'][:2])
                det['z_trans'] = det['translation'][-1]
                det['tracking'] = np.array(det['velocity'][:2]) * -1 * time_lag
                # if model is not CenterPoint
                if len(det['tracking']) == 0:
                    det['tracking'] = np.zeros((2,)).astype(np.float32)
                det['label_preds'] = g.gt_labels[det['detection_name']]
                temp.append(det)

            results = temp

        N = len(results)
        M = len(self.tracks)

        # N X 2 
        if 'tracking' in results[0]:
            dets = np.array(
            [ det['ct'] + det['tracking'].astype(np.float32)
             for det in results], np.float32)
        else:
            dets = np.array(
                [det['ct'] for det in results], np.float32) 

        item_cat = np.array([item['label_preds'] for item in results], np.int32) # N
        track_cat = np.array([track['label_preds'] for track in self.tracks], np.int32) # M

        error = []
        for box in results:
            if box['detection_name'] in self.CLS_VELOCITY_ERROR.keys():
                error.append(self.CLS_VELOCITY_ERROR[box['detection_name']])
            else:
                error.append(5)

        max_diff = np.array(error, np.float32)

        tracks = np.array(
            [pre_det['ct'] for pre_det in self.tracks], np.float32) # M x 2

        if len(tracks) > 0:    # NOT FIRST FRAME
            dist = (((tracks.reshape(1, -1, 2) - \
                dets.reshape(-1, 1, 2)) ** 2).sum(axis=2))    # N x M
            dist = np.sqrt(dist) # absolute distance in meter

            invalid = ((dist > max_diff.reshape(N, 1)) + \
                (item_cat.reshape(N, 1) != track_cat.reshape(1, M))) > 0

            dist = dist + invalid * 1e18
            
            matched_indices = self.greedy_assignment(copy.deepcopy(dist))
        else:    # first few frame
            assert M == 0
            matched_indices = np.array([], np.int32).reshape(-1, 2)

        unmatched_dets = [d for d in range(dets.shape[0]) \
            if not (d in matched_indices[:, 0])]

        unmatched_tracks = [d for d in range(tracks.shape[0]) \
            if not (d in matched_indices[:, 1])]
        

        matches = matched_indices

        ret = []
        for m in matches:
            track = results[m[0]]
            track['tracking_id'] = self.tracks[m[1]]['tracking_id']            
            track['age'] = 1
            track['active'] = self.tracks[m[1]]['active'] + 1
            ret.append(track)

        for i in unmatched_dets:
            track = results[i]
            self.id_count += 1
            track['tracking_id'] = self.id_count
            track['age'] = 1
            track['active'] = 1
            ret.append(track)

        # still store unmatched tracks if its age doesn't exceed max_age, however, we shouldn't output 
        # the object in current frame 
        for i in unmatched_tracks:
            track = self.tracks[i]
            if track['age'] < self.max_age:
                track['age'] += 1
                track['active'] = 0
                ct = track['ct']

                # movement in the last second
                if 'tracking' in track:
                    offset = track['tracking'] * -1 # move forward 
                    track['ct'] = ct + offset 
                ret.append(track)

        self.tracks = ret
        return ret