import cv2
import pytesseract
import timeit
import numpy  as np

# Set the path for tesseract executable

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Start capturing the webcam feed
cap = cv2.VideoCapture(0)

while(True):
    # Capture img-by-img
    start_time = timeit.default_timer()

    ret, frame = cap.read()
    cv2.imwrite('frame_sample.jpg', frame)


    # Convert the image from OpenCV BGR format to matplotlib RGB format
    # to display the image    
    
    # Convert to gray
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


    # # Resize image
    img = cv2.resize(gray, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)

    # # Denoise
    img = cv2.fastNlMeansDenoising(img)
    
    # Configure Tesseract to use the original engine only
    custom_config = '--oem 3'
    # Run tesseract OCR on image
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=custom_config)

    # Find bounding box around "WATER"
    num_boxes = len(data['text'])
    print("length:"+str(num_boxes)+":"+str(data['text']))
    for i in range(num_boxes):
        if data['text'][i].upper() == "WATER":
            (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
            # img = cv2.rectangle(img, (x, y-1050), (x + w, y + h), (0, 255, 0), 2)
            padding_y = h*8
            img = cv2.rectangle(img, (x, y-padding_y), (x + w, y + h), (0, 255, 0), 2)

        if data['text'][i].upper() == "WASTE":
            (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
            # img = cv2.rectangle(img, (x, y-1050), (x + w, y + h), (0, 255, 0), 2)
            img = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 0), 2)
            
        if data['text'][i].upper() == "SUPPLY":
            (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
            # img = cv2.rectangle(img, (x, y-1050), (x + w, y + h), (0, 255, 0), 2)
            img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
        
        if data['text'][i].upper() == "PWR":
            (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
            # img = cv2.rectangle(img, (x, y-1050), (x + w, y + h), (0, 255, 0), 2)
            img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 255), 2)
    

    end_time = timeit.default_timer()

    # Calculate the duration in milliseconds
    duration = (end_time - start_time) * 1000

    print(f"Time taken: {duration} milliseconds")

    # Display the resulting img
    cv2.imshow('img', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
    # time.sleep(2)

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
