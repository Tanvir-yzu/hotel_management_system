
Table "hotel_roomtype" {
  "id" INT [pk, not null, increment]
  "type_name" VARCHAR(10) [unique, not null]
  "price_per_night" DECIMAL(10,2) [not null]
  "description" TEXT
  "capacity" INT [not null]
  "amenities" TEXT
}

Table "hotel_room" {
  "id" INT [pk, not null, increment]
  "room_number" VARCHAR(10) [unique, not null]
  "room_type_id" INT [not null]
  "is_available" BOOLEAN [not null]
  "floor_number" INT [not null]
  "room_size" DECIMAL(5,2) [not null]
  "has_balcony" BOOLEAN [not null]
  "has_view" BOOLEAN [not null]
  "view_description" VARCHAR(100)
}

Table "hotel_guest" {
  "id" INT [pk, not null, increment]
  "name" VARCHAR(100) [not null]
  "email" VARCHAR(254) [unique, not null]
  "phone_number" VARCHAR(20)
  "address" TEXT
  "id_number" VARCHAR(20)
  "date_of_birth" DATE
  "registration_date" DATETIME [not null]
  "is_vip" BOOLEAN [not null]
}

Table "hotel_booking" {
  "id" INT [pk, not null, increment]
  "room_id" INT [not null]
  "guest_id" INT
  "check_in_date" DATE [not null]
  "check_out_date" DATE [not null]
  "booking_date" DATETIME [not null]
  "status" VARCHAR(20) [not null]
  "guest_name" VARCHAR(100)
  "guest_email" VARCHAR(254)
  "special_requests" TEXT
  "number_of_guests" INT [not null]
  "total_price" DECIMAL(10,2)
  "is_paid" BOOLEAN [not null]
  "payment_method_used" VARCHAR(50)
}

Table "hotel_payment" {
  "id" INT [pk, not null, increment]
  "booking_id" INT [unique, not null]
  "amount_paid" DECIMAL(10,2) [not null]
  "payment_type" VARCHAR(10) [not null]
  "payment_method_type" VARCHAR(20) [not null]
  "payment_date" DATETIME [not null]
  "payment_method" VARCHAR(50) [not null]
  "transaction_id" VARCHAR(100)
  "payment_reference" VARCHAR(100)
  "receipt_url" VARCHAR(200)
}

Table "hotel_roomservice" {
  "id" INT [pk, not null, increment]
  "booking_id" INT [not null]
  "service_name" VARCHAR(100) [not null]
  "description" TEXT
  "quantity" INT [not null]
  "price_per_unit" DECIMAL(10,2) [not null]
  "service_date" DATETIME [not null]
  "status" VARCHAR(20) [not null]
}

Table "hotel_housekeeping" {
  "id" INT [pk, not null, increment]
  "room_id" INT [not null]
  "cleaning_date" DATE [not null]
  "cleaning_time" TIME [not null]
  "status" VARCHAR(20) [not null]
  "notes" TEXT
}

Table "hotel_maintenancerequest" {
  "id" INT [pk, not null, increment]
  "room_id" INT [not null]
  "request_date" DATETIME [not null]
  "description" TEXT [not null]
  "status" VARCHAR(20) [not null]
  "resolution_notes" TEXT
}

Table "hotel_review" {
  "id" INT [pk, not null, increment]
  "booking_id" INT [unique, not null]
  "rating" INT [not null]
  "comment" TEXT
  "review_date" DATETIME [not null]
  "is_public" BOOLEAN [not null]
}

Ref:"hotel_roomtype"."id" < "hotel_room"."room_type_id" [delete: cascade]

Ref:"hotel_room"."id" < "hotel_booking"."room_id" [delete: cascade]

Ref:"hotel_guest"."id" < "hotel_booking"."guest_id" [delete: set null]

Ref:"hotel_booking"."id" < "hotel_payment"."booking_id" [delete: cascade]

Ref:"hotel_booking"."id" < "hotel_roomservice"."booking_id" [delete: cascade]

Ref:"hotel_room"."id" < "hotel_housekeeping"."room_id" [delete: cascade]

Ref:"hotel_room"."id" < "hotel_maintenancerequest"."room_id" [delete: cascade]

Ref:"hotel_booking"."id" < "hotel_review"."booking_id" [delete: cascade]
