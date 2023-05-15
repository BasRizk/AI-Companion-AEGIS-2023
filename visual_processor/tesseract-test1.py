
import cv2
import pytesseract
from pytesseract import Output

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


##  procesing starts
# Load image
# img = cv2.imread('C:/Users/prashant/Documents/homography/UIA/SUITS_UIA_PANEL.jpg')
img = cv2.imread('basem.jpg',cv2.COLOR_BGR2GRAY)


# # Resize image
img = cv2.resize(img, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)

# # Denoise
img = cv2.fastNlMeansDenoising(img)

# cv2.imwrite('processed_image-1.jpg', img)
# # Thresholding
# # _, img = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# img = cv2.imread('processed_image-1.jpg', cv2.IMREAD_GRAYSCALE)

# # Save the processed image
# cv2.imwrite('processed_image.jpg', img)

# ## processing ends
# # Read the image
# img = cv2.imread('processed_image.jpg')
# img = cv2.imread('UIA-1/train/images/IMG_3859_jpg.rf.efb6a2550e28f4a63589b7f891f951b4.jpg')

# Convert to gray
# img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Run tesseract OCR on image
data = pytesseract.image_to_data(img, output_type=Output.DICT, config='--psm 6')

# Find bounding box around "WATER"
num_boxes = len(data['text'])
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

# Show the image
cv2.imwrite('processed_image_final.jpg', img)

# cv2.imshow('img', img) 
 
# cv2.waitKey(0)
