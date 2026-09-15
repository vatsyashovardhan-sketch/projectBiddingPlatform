// One-off backfill: denormalize seller/listing ratings from reviews.
// Run: mongosh --quiet backfill_ratings.js
db = db.getSiblingDB('projectbidding');
var sag = db.reviews.aggregate([{$group: {_id: '$seller_id', avg: {$avg: '$rating'}, n: {$sum: 1}}}]).toArray();
sag.forEach(function (a) {
  var v = Math.round(a.avg * 100) / 100;
  db.listings.updateMany({seller_id: a._id}, {$set: {seller_rating: v, seller_rating_count: a.n}});
});
var lag = db.reviews.aggregate([{$group: {_id: '$listing_id', avg: {$avg: '$rating'}, n: {$sum: 1}}}]).toArray();
lag.forEach(function (a) {
  var v = Math.round(a.avg * 100) / 100;
  db.listings.updateOne({_id: a._id}, {$set: {rating: v, rating_count: a.n, rating_weighted: v}});
});
print('sellers updated: ' + sag.length + ', listings updated: ' + lag.length);
