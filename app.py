from flask import Flask, render_template, request, jsonify
import pickle
import numpy as np
import os
import gdown

# ================= DOWNLOAD PKL FILES =================

files = {
    "popular.pkl": "1DsKw7vyMXs7Y4G0BSTynDM6CmmvvACAT",
    "pt.pkl": "1qZCNwCih9GeLKpicGdO535nB71sxS3UD",
    "books.pkl": "1U3clgcqNZu7sp2c0tJjeb2s34lfEGY7y",
    "similarity_scores.pkl": "1Zkppl8DewO3OtMfOAVxDKcvVEytaYbUK"
}

def download_file(filename, file_id):
    try:
        if not os.path.exists(filename):
            print(f"Downloading {filename}...")
            url = f"https://drive.google.com/uc?id={file_id}"
            gdown.download(url, filename, quiet=False)
    except Exception as e:
        print(f"Error downloading {filename}: {e}")

for filename, file_id in files.items():
    download_file(filename, file_id)

print("All model files ready ✅")

# ================= LOAD DATA =================

try:
    popular_df = pickle.load(open('popular.pkl', 'rb'))
    pt = pickle.load(open('pt.pkl', 'rb'))
    books = pickle.load(open('books.pkl', 'rb'))
    similarity_scores = pickle.load(open('similarity_scores.pkl', 'rb'))
except Exception as e:
    print("Error loading pickle files:", e)

# ================= CLEAN DATA =================

pt = pt.copy()
pt.index = pt.index.astype(str).str.strip()
pt = pt[~pt.index.isna()]

books['Book-Title'] = books['Book-Title'].astype(str).str.strip()

# ================= INIT APP =================

app = Flask(__name__)

# ================= HOME =================

@app.route('/')
def index():
    return render_template(
        'index.html',
        book_name=list(popular_df['Book-Title'].values),
        author=list(popular_df['Book-Author'].values),
        image=list(popular_df['Image-URL-M'].values),
        votes=list(popular_df['num_ratings'].values),
        rating=list(popular_df['avg_rating'].values)
    )

# ================= RECOMMEND PAGE =================

@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')

# ================= AUTOCOMPLETE =================

@app.route('/autocomplete')
def autocomplete():
    try:
        query = request.args.get('q', '').lower().strip()

        if not query:
            return jsonify([])

        suggestions = [
            str(book)
            for book in pt.index.tolist()
            if query in str(book).lower()
        ]

        return jsonify(suggestions[:8])
    except Exception as e:
        print("Autocomplete error:", e)
        return jsonify([])

# ================= RECOMMENDATION =================

@app.route('/recommend_books', methods=['POST'])
def recommend():
    try:
        user_input = request.form.get('user_input', '')
        user_input = str(user_input).strip()

        if not user_input:
            return render_template('recommend.html', data=[])

        if user_input not in pt.index.tolist():
            return render_template('recommend.html', data=[], error="Book not found!")

        try:
            index = pt.index.tolist().index(user_input)
        except ValueError:
            return render_template('recommend.html', data=[], error="Book not found!")

        # safe similarity access
        if index >= len(similarity_scores):
            return render_template('recommend.html', data=[], error="Data error")

        similar_items = sorted(
            list(enumerate(similarity_scores[index])),
            key=lambda x: x[1],
            reverse=True
        )[1:5]

        data = []

        for i in similar_items:
            try:
                temp_df = books[books['Book-Title'] == pt.index[i[0]]]
                temp_df = temp_df.drop_duplicates('Book-Title')

                if temp_df.empty:
                    continue

                item = [
                    temp_df['Book-Title'].values[0],
                    temp_df['Book-Author'].values[0],
                    temp_df['Image-URL-M'].values[0]
                ]

                data.append(item)

            except Exception as e:
                print("Error in recommendation loop:", e)
                continue

        return render_template('recommend.html', data=data)

    except Exception as e:
        print("Recommendation error:", e)
        return render_template('recommend.html', data=[], error="Something went wrong")

# ================= RUN =================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)