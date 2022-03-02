IMAGE_IDS = {
            "11": "one", "12": "two", "13": "three",
            "14": "four", "15": "five", "16": "six",
            "17": "seven", "18": "eight", "19": "nine",
            "20": "Alphabet A", "21": "Alphabet B", "22": "Alphabet C",
            "23": "Alphabet D", "24": "Alphabet E", "25": "Alphabet F",
            "26": "Alphabet G", "27": "Alphabet H", "28": "Alphabet S",
            "29": "Alphabet T", "30": "Alphabet U", "31": "Alphabet V", 
            "32": "Alphabet W", "33": "Alphabet X", "34": "Alphabet Y", 
            "35": "Alphabet Z", "36": "Up arrow", "37": "Down arrow", 
            "38": "Right arrow", "39": "Left arrow", "40": "Stop",
            "41": "Bulls eye"
        }

MODEL_URL = "https://drive.google.com/uc?id=1EIWIDC2ntZ3D9DE9vWOip7c-6T_0YrT-"

# in the formats {"height": "distance"}
# so when calling, if bbox is bigger than height, then it is considered 
# this distance away
DISTANCE_BOX_SIZE = {
    190: 15,
    170: 20,
    150: 25,
    133: 30, 
    117: 35,
    95: 40,
    78: 50,
    72: 55,
    64: 60,
    61: 65,
    58: 70,
    0: 75,
}
