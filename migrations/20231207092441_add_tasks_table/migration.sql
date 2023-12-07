-- CreateTable
CREATE TABLE "Tasks" (
    "user_id" INTEGER NOT NULL,
    "chat_id" INTEGER NOT NULL,
    "team_id" INTEGER NOT NULL,
    "team_name" TEXT NOT NULL,
    "team_status" TEXT NOT NULL,
    "msg" TEXT NOT NULL,
    "is_question" BOOLEAN NOT NULL,
    "call_counter" INTEGER NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Tasks_pkey" PRIMARY KEY ("team_id")
);
