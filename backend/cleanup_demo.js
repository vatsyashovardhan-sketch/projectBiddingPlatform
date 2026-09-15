db = db.getSiblingDB('projectbidding');
uids = db.users.find({email: /^demo-(seller|buyer)@test\.com$/}, {_id: 1}).toArray().map(u => u._id);
print('demo/test users: ' + uids.length);
uids.forEach(function (id) {
  db.listings.deleteMany({seller_id: id});
  db.orders.deleteMany({$or: [{seller_id: id}, {buyer_id: id}]});
  db.bids.deleteMany({$or: [{seller_id: id}, {buyer_id: id}]});
  db.reviews.deleteMany({$or: [{seller_id: id}, {buyer_id: id}]});
  db.users.deleteOne({_id: id});
});
print('after: users=' + db.users.countDocuments() + ' listings=' + db.listings.countDocuments());
