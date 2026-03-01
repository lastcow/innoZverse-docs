# Redis

Redis is an in-memory data store used for caching, session management, pub/sub, and real-time features.

## Core Data Types

```bash
# String
SET user:1:name "Alice"
GET user:1:name
SET counter 0
INCR counter          # Atomic increment → 1
INCRBY counter 5      # → 6
EXPIRE session:abc 3600    # Expire in 1 hour
TTL session:abc       # Check remaining time

# Hash (like a dictionary/object)
HSET user:1 name "Alice" email "alice@example.com" age 30
HGET user:1 name
HGETALL user:1
HMSET user:2 name "Bob" email "bob@example.com"

# List
LPUSH queue "task1" "task2"    # Push to left
RPUSH queue "task3"             # Push to right
LPOP queue                     # Pop from left (FIFO queue)
LRANGE queue 0 -1              # Get all elements
LLEN queue                     # Length

# Set (unique values)
SADD online:users "user1" "user2" "user3"
SMEMBERS online:users
SISMEMBER online:users "user1"    # Check membership
SCARD online:users               # Count

# Sorted Set (with scores)
ZADD leaderboard 1000 "alice" 850 "bob" 1200 "carol"
ZREVRANGE leaderboard 0 9 WITHSCORES    # Top 10
ZRANK leaderboard "alice"               # Rank
ZINCRBY leaderboard 50 "alice"          # Add points
```

## Caching Pattern (Python)

```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def get_user(user_id):
    # Check cache first
    cache_key = f"user:{user_id}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    # Cache miss — query database
    user = db.query(f"SELECT * FROM users WHERE id = {user_id}")

    # Store in cache for 1 hour
    r.setex(cache_key, 3600, json.dumps(user))
    return user

def invalidate_user_cache(user_id):
    r.delete(f"user:{user_id}")
```

## Pub/Sub Messaging

```python
# Publisher
r.publish('notifications', json.dumps({
    'type': 'order_shipped',
    'order_id': 12345,
    'tracking': '1ZY549V703718...'
}))

# Subscriber
pubsub = r.pubsub()
pubsub.subscribe('notifications')
for message in pubsub.listen():
    if message['type'] == 'message':
        data = json.loads(message['data'])
        print(f"Received: {data}")
```
