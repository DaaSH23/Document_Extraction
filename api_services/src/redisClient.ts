import Redis from "ioredis";

const publisherClient = new Redis(); // for queue operations like lpush
const subscriberClient = new Redis(); // for subscription

export { publisherClient, subscriberClient };