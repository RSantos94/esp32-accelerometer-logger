import cv2
import imutils

import csv

from camera_calibration import CameraCalibration
from centroidTracker import CentroidTracker


class BackgroundSubtractionKNN:
    outputFrame = None

    def __init__(self, source_name):
        self.video_name = 'video_files/' + source_name + '.MP4'
        self.ct = CentroidTracker()
        self.centroid_file = 'results/' + source_name + '-centroids.csv'
        self.window_size = (640, 360)
        #self.window_size = (1280, 720)

    def subtractor(self, lock, area):
        camera_calibration = CameraCalibration(self.video_name)
        camera_calibration.calibrate(lock)
        cap = cv2.VideoCapture(self.video_name)
        # cap = cv2.VideoCapture('E:/Pictures & Videos/Videos/GoPro/GH010347.MP4')
        # cap = cv2.VideoCapture('video_files/PXL_20210522_093608367.mp4')
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 40)
        # cap2.set(cv2.CAP_PROP_BUFFERSIZE, 40)

        success, img = cap.read()

        # myvideo=cv2.VideoWriter("video_files/forgroundKNN.avi", cv2.VideoWriter_fourcc('M','J','P','G'), 30, (int(img.shape[1]),int(img.shape[0])))

        BS_KNN = cv2.createBackgroundSubtractorKNN(history=20, detectShadows=False, dist2Threshold=5000)
        #BS_KNN = cv2.createBackgroundSubtractorMOG2(history=10, detectShadows=False, varThreshold=100)
        # BS_KNN = cv2.createBackgroundSubtractorMOG2()

        # tracker = cv2.TrackerMOSSE_create()
        while cap.isOpened():
            # timer = cv2.getTickCount()
            success, img = cap.read()
            # success2, img2 = cap2.read()

            # fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer)
            # cv2.putText(img, str(int(cap.get(cv2.CAP_PROP_FPS))), (75, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            # cv2.putText(img2, str(int(cap2.get(cv2.CAP_PROP_FPS))), (75, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if img is not None:
                #cv2.namedWindow("Pier cam", cv2.WINDOW_NORMAL)  # Create window with freedom of dimensions

                imS = cv2.resize(img, self.window_size)  # Resize image
                # imS2 = cv2.resize(img2, (960, 540))  # Resize image

                cv2.rectangle(imS, (10, 2), (100, 20), (255, 255, 255), -1)
                cv2.putText(imS, str(cap.get(cv2.CAP_PROP_POS_FRAMES)), (15, 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0))

                cv2.imshow("Pier cam", imS)
                # cv2.imshow("Pier cam 2", imS2)

                # cv2.namedWindow("Pier cam undistorted", cv2.WINDOW_NORMAL)
                # undistorted_img = camera_calibration.undistort(img)

                img_denoise = None

                # cv2.fastNlMeansDenoising(src=img, dst=img_denoise, h=2)
                # if undistorted_img is not None:
                # cv2.imshow("Pier cam undistorted", undistorted_img)
                # fgKnn = BS_KNN.apply(undistorted_img)

                # if img_denoise is not None:
                # fgKnn = BS_KNN.apply(img_denoise)
                # cv2.imshow("Pier cam undistorted", img_denoise)

                fgKnn = BS_KNN.apply(img)

                thresh = cv2.threshold(fgKnn, 25, 255, cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=4)

                # fg = cv2.copyTo(img, fgKnn)
                # myvideo.write(fg)

                fgKnnRs = self.select_objects(area, cap, thresh)

            if cv2.waitKey(1) & 0xff == ord('q'):
                break

        # self.save_centroids()
        cv2.destroyAllWindows()
        cap.release()

    def select_objects(self, area, cap, fgKnn):
        if fgKnn is not None:
            # fgKnnRs = cv2.resize(fgKnn, (960, 540))  # Resize image
            fgKnnRs = fgKnn  # No resize image

            cv2.rectangle(fgKnnRs, (10, 2), (140, 20), (255, 255, 255), -1)
            cv2.putText(fgKnnRs, str(cap.get(cv2.CAP_PROP_POS_FRAMES)), (15, 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0))
            cv2.putText(fgKnnRs, str(int(cap.get(cv2.CAP_PROP_FPS))), (75, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 0, 0))


            fgKnnRs = self.get_centroid(area, fgKnnRs, cap)

            #cv2.namedWindow("Foreground", cv2.WINDOW_NORMAL)
            cv2.imshow("Foreground", cv2.resize(fgKnnRs, self.window_size))
        return fgKnnRs

    def get_centroid(self, area, fgKnnRs, cap):
        (contours, hierarchy) = cv2.findContours(fgKnnRs.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        rects = []

        i = 0
        #while  i< len(contours):
            #i = hierarchy[i][0]
            #c = contours[i]
        for idx, c in enumerate(contours):
            if cv2.contourArea(c) < area:
                continue

            if hierarchy[0, idx, 3] == -1:
                continue
            print (hierarchy[0, idx, 3] )

            # get bounding box from countour
            (x, y, w, h) = cv2.boundingRect(c)

            # draw bounding box
            cv2.rectangle(fgKnnRs, (x, y), (x + w, y + h), (100, 0, 255), 2)

            rects.append([x, y, x + w, y + h])

            # moments = cv2.moments(c)
            # cX = int(moments["m10"] / moments["m00"])
            # cY = int(moments["m01"] / moments["m00"])
            # # draw the contour and center of the shape on the image
            # cv2.drawContours(fgKnnRs, [c], -1, (0, 255, 0), 2)
            # cv2.circle(fgKnnRs, (cX, cY), 7, (255, 255, 255), -1)
            # print(cX)
            # print(cY)
            # cv2.putText(fgKnnRs, "center", (cX - 20, cY - 20),
            #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # update our centroid tracker using the computed set of bounding
        # box rectangles
        objects = self.ct.update(rects)

        if objects is not None:
            with open(self.centroid_file, 'w', encoding='UTF8') as f:
                writer = csv.writer(f)
                for (objectID, centroid) in objects.items():
                    # draw both the ID of the object and the centroid of the
                    # object on the output frame
                    text = "ID {}".format(objectID)
                    cv2.putText(fgKnnRs, text, (centroid[0] - 10, centroid[1] - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 0, 255), 2)
                    cv2.circle(fgKnnRs, (centroid[0], centroid[1]), 4, (100, 0, 255), -1)

                    position_text = str(cap.get(cv2.CAP_PROP_POS_FRAMES)) + ", " + str(objectID) + ", {" + str(centroid[0]) + "}, {" + str(centroid[1]) + "}"
                    writer.writerow(position_text)

        return fgKnnRs

    def create_centroids_file(self):
        with open(self.centroid_file, 'w', encoding='UTF8') as f:
            writer = csv.writer(f)
            writer.writerow("Object ID, x , y")

    def save_centroids(self):
        with open(self.centroid_file, 'w', encoding='UTF8') as f:
            writer = csv.writer(f)
            writer.writerow('Object ID, x , y')
            for (objectID, centroid) in self.ct.objects.items():
                text = objectID + ", " + centroid[0] + ", " + centroid[1]
                writer.writerow(text)
