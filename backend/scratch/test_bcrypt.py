import bcrypt
import time

password = "officer123"
start = time.time()
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
print(f"Hashing took: {time.time() - start:.4f}s")

start = time.time()
match = bcrypt.checkpw(password.encode(), hashed)
print(f"Check took: {time.time() - start:.4f}s")
print(f"Match: {match}")
