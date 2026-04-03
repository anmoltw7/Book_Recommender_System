from flask import Flask, render_template, request, jsonify
import pickle
import numpy as np
import os
import gdown
import sys

# ================= DOWNLOAD PKL FILES =================

files = {
    "popular.pkl": "1DsKw7vyMXs7Y4G0BSTynDM6CmmvvACAT",
    "pt.pkl": "1qZCNwCih9GeLKpicGdO535nB71sxS3UD",
    "books.pkl": "1U3clgcqNZu7sp2c0tJjeb2s34lfEGY7y",
    "similarity_scores.pkl": "1Zkppl8DewO3OtMfOAVxDKcvVEytaYbUK"
}


def download_file(filename, file_id):
    try:
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            print(f"Downloading {filename}...")
            url = f"https://drive.google.com/uc?id={file_id}"
            gdown.download(url, filename, quiet=False)
    except Exception as e:
        print(f"Error downloading {filename}: {e}")


for filename, file_id in files.items():
    download_file(filename, file_id)

print("All model files check complete ✅")

# ================= LOAD DATA =================

try:
    # We define these as None first to prevent NameErrors later
    popular_df = None
    pt = None
    books = None
    similarity_scores = None

    popular_df = pickle.load(open('popular.pkl', 'rb'))
    pt = pickle.load(open('pt.pkl', 'rb'))
    books = pickle.load(open('books.pkl', 'rb'))
    similarity_scores = pickle.load(open('similarity_scores.pkl', 'rb'))

    print("Files loaded successfully! 🚀")

except Exception as e:
    print(f"\n❌ FATAL ERROR: Could not load pickle files: {e}")
    print("Check if the files downloaded correctly or if the Google Drive links are still active.")
    sys.exit(1)  # Stop the script here so it doesn't crash on line 51

# ================= CLEAN DATA =================

# Now this is safe because we know 'pt' exists
pt = pt.copy()
pt.index = pt.index.astype(str).str.strip()
pt = pt[~pt.index.isna()]

books['Book-Title'] = books['Book-Title'].astype(str).str.strip()

# ================= INIT APP =================

app = Flask(__name__)


# ================= ROUTES =================

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


@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')


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


@app.route('/recommend_books', methods=['POST'])
def recommend():
    try:
        user_input = request.form.get('user_input', '').strip()

        if not user_input or user_input not in pt.index:
            return render_template('recommend.html', data=[], error="Book not found!")

        index = np.where(pt.index == user_input)[0][0]

        similar_items = sorted(
            list(enumerate(similarity_scores[index])),
            key=lambda x: x[1],
            reverse=True
        )[1:6]

        data = []
        for i in similar_items:
            temp_df = books[books['Book-Title'] == pt.index[i[0]]]
            temp_df = temp_df.drop_duplicates('Book-Title')

            if not temp_df.empty:
                item = [
                    temp_df['Book-Title'].values[0],
                    temp_df['Book-Author'].values[0],
                    temp_df['Image-URL-M'].values[0]
                ]
                data.append(item)

        return render_template('recommend.html', data=data)

    except Exception as e:
        print("Recommendation error:", e)
        return render_template('recommend.html', data=[], error="Something went wrong")


# ================= RUN =================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 4000))
    # Fixed the syntax error here (removed the trailing dot)
    app.run(host="0.0.0.0", port=port)