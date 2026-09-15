db = db.getSiblingDB('projectbidding');
uids = db.users.find({email: /@example\.com$/}, {_id: 1}).toArray().map(u => u._id);
print('seed users found: ' + uids.length);
if (uids.length > 0) {
  tids = db.threads.find({$or: [{seller_id: {$in: uids}}, {buyer_id: {$in: uids}}]}, {_id: 1}).toArray().map(t => t._id);
  db.messages.deleteMany({thread_id: {$in: tids}});
  db.users.deleteMany({_id: {$in: uids}});
  db.listings.deleteMany({seller_id: {$in: uids}});
  db.orders.deleteMany({$or: [{seller_id: {$in: uids}}, {buyer_id: {$in: uids}}]});
  db.bids.deleteMany({$or: [{seller_id: {$in: uids}}, {buyer_id: {$in: uids}}]});
  db.reviews.deleteMany({$or: [{seller_id: {$in: uids}}, {buyer_id: {$in: uids}}]});
  db.threads.deleteMany({$or: [{seller_id: {$in: uids}}, {buyer_id: {$in: uids}}]});
  db.payouts.deleteMany({seller_id: {$in: uids}});
  db.notifications.deleteMany({user_id: {$in: uids}});
  db.follows.deleteMany({$or: [{by: {$in: uids}}, {target: {$in: uids}}]});
  db.reports.deleteMany({$or: [{by: {$in: uids}}, {target: {$in: uids}}]});
  db.resets.deleteMany({user_id: {$in: uids}});
  db.verifies.deleteMany({user_id: {$in: uids}});
}
print('after: users=' + db.users.countDocuments() + ' listings=' + db.listings.countDocuments());
