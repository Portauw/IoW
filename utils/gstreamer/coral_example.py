import gstreamer
import cv2

def main():

    def my_user_callback(latest_frame):
      print(latest_frame)
      cv2.imshow('Example - Show image in window',latest_frame)
      #cv2.waitKey(1) # waits until a key is pressed

    result = gstreamer.run_pipeline(my_user_callback,
                                    src_size=(640, 480),
                                    appsink_size=(300, 300),
                                    videosrc="/dev/video0",
                                    videofmt="raw")

if __name__ == '__main__':
    main()
