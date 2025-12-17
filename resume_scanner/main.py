import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re 
import string

df = pd.read_csv("UpdatedResumeDataSet.csv")

print(df.head())
print(df.shape)

counts = df['Category'].value_counts()

print(counts)

labels = df['Category'].unique()

# plt.pie(counts, labels=labels)

def cleanResume(txt):
    
    cleanTxt = re.sub(r'http\S+', ' ', txt)
    cleanTxt = re.sub(r'@\S+', '', cleanTxt)
    cleanTxt = re.sub(r'#\S+', '', cleanTxt)
    cleanTxt = re.sub(r'RT||cc', '', cleanTxt)
    # cleanTxt = re.sub(r'[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), '', cleanTxt)
    cleanTxt = re.sub(rf"[{re.escape(string.punctuation)}]", "", cleanTxt)
    cleanTxt = re.sub(r'[^\x00-\x7f]', '', cleanTxt)
    cleanTxt = re.sub(r'\s+', ' ', cleanTxt)
    
    return cleanTxt

# print(cleanResume("My name is Ansh and http://ansh.com/ yes no @026.com"))

print(df.head())

df['newResume'] = df['Resume'].apply(lambda x: cleanResume(x))

# print(df.head())


# print(df['Resume'][0])
# print(df['clearResume'][0])

from sklearn.preprocessing import LabelEncoder

le = LabelEncoder()

print(df['Category'].unique())

le.fit(df['Category'])
df['newCategory'] = le.transform(df['Category'])

print(df.head())
print(df['newCategory'].unique())
