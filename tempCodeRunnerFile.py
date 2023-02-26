myFile.close()
myFile = open('data.csv', 'r')
print("The content of the csv file is:")
print(myFile.read())