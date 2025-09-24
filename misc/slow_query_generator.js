db = db.getSiblingDB("Restaurant");
db.setProfilingLevel(0, 0);
db.pizzas.drop();
db.pizzas.insertMany([
    { _id: 3, type: 'beef', size: 'medium', price: 6 },
    { _id: 1, type: 'cheese', size: 'medium', price: 8 },
    { _id: 2, type: 'tofu', size: 'small', price: 4 },
    { _id: 4, type: 'sausage', size: 'large', price: 10 },
    { _id: 5, type: 'pineapple', size: 'large', price: 100 }
])
db.pizzas.createIndex({ type: 1 });

db.pizzas.find({ type: 'beef' });
db.pizzas.find({ type: 'beef' }).sort({price: -1});
db.pizzas.find({ 
    size: { 
        $in: ["small", "medium", "large"] 
    } 
});
iter = db.pizzas.find({ 
    size: { 
        $in: ["small", "medium", "large"] 
    } 
}).batchSize(1);
while (iter.hasNext()) { iter.next(); }
db.pizzas.find({ 
    size: { 
        $in: ["small", "medium", "large"] 
    } 
}).sort({ price: -1 });
db.pizzas.find({ 
    size: { 
        $in: ["small", "medium", "large"] 
    } 
}).sort({ type: 1 });

db.pizzas.aggregate([
    { $match: { size: { $in: ["small", "medium", "large"] } } },
    { $group: { _id: "$size", count: { $sum: 1 } } },
    { $sort: { count: -1 } }
])
db.setProfilingLevel(0, 100);