import csv

import cameratransform as ct
import numpy as np

from cameraTransformation import CameraTransformation
from os.path import exists


def get_points(source):
    f = open('config/' + source + '-points.txt', "r")
    landmarks = []
    for x in f:
        x = x.replace("\n", "")
        arr = x.split(',')
        array = [float(arr[0].strip()), float(arr[1].strip())]
        landmarks.append(array)

    return landmarks


class StereoProcessing:

    def __init__(self, source1, source2):
        self.centroid_file_1 = 'results/' + source1 + '-centroids.csv'
        self.centroid_file_2 = 'results/' + source2 + '-centroids.csv'
        self.objects_to_track1 = []
        self.objects_to_track2 = []

        ct1 = CameraTransformation(source1)
        ct1.configure()
        cam1 = ct1.camera
        ct2 = CameraTransformation(source1)
        ct2.configure()
        cam2 = ct2.camera

        self.cam_group = ct.CameraGroup(cam1.projection, (cam1.orientation, cam2.orientation))


    def execute(self):
        centroids1 = self.read_file(self.centroid_file_1, self.objects_to_track_1)
        centroids2 = self.read_file(self.centroid_file_2, self.objects_to_track_2)

        fps = None
        object_id = None

        prev1 = []
        prev2 = []

        object_start_pos1 = []
        object_end_pos1 = []
        object_start_pos2 = []
        object_end_pos2 = []
        frames = []
        for row1 in centroids1:
            for row2 in centroids2:
                if object_id is None and row1['Object ID'] == row2['Object ID'] and row1['frame'] == row2['frame']:
                    if fps is None:
                        fps = int(row1['fps'])
                    object_id = row1['Object ID']
                    prev1 = [float(row1['x']), float(row1['y'])]
                    prev2 = [float(row2['x']), float(row1['y'])]

                    object_start_pos1 = []
                    object_end_pos1 = []
                    object_start_pos2 = []
                    object_end_pos2 = []
                    frames = []
                    continue

                if object_id == row1['Object ID'] and row1['Object ID'] == row2['Object ID'] and row1['frame'] == row2[
                    'frame']:
                    object_start_pos1.append(prev1)
                    object_start_pos2.append(prev2)

                    pos1 = [float(row1['x']), float(row1['y'])]
                    prev1 = pos1
                    pos2 = [float(row2['x']), float(row1['y'])]
                    prev2 = pos2

                    object_end_pos1.append(pos1)
                    object_end_pos2.append(pos2)
                    frames.append(int(row1['frame']))



                else:
                    points1_start = np.array(object_start_pos1)
                    points1_end = np.array(object_end_pos1)
                    points2_start = np.array(object_start_pos2)
                    points2_end = np.array(object_end_pos2)

                    points_start_3D = self.cam_group.spaceFromImages(points1_start, points2_start)
                    points_end_3D = self.cam_group.spaceFromImages(points1_end, points2_end)

                    distances = np.linalg.norm(points_end_3D - points_start_3D, axis=-1)
                    print('Object ' + object_id + ' total distance is: ' + str(distances))
                    object_id = None

    def read_file(self, centroid_file, objects):
        with open(centroid_file, encoding='UTF8') as f:
            reader = csv.DictReader(f)
            result = sorted(reader, key=lambda d: int(d['Object ID']))

            object_id = None
            prev_x = None
            prev_y = None
            dist = 0.0

            if objects is not None and isinstance(objects, list):
                return [a for a in result if a['Object ID'] in objects]
            else:
                return result

    def configure_points(self, source1, source2):
        corresponding1 = np.array(get_points(source1))
        corresponding2 = np.array(get_points(source2))

        self.cam_group.addPointCorrespondenceInformation(corresponding1, corresponding2)

    def has_points_file(self, source):
        return exists('config/' + source + '-points.txt')
