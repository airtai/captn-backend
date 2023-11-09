-- CreateTable
CREATE TABLE "GAuth" (
    "id" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "user_id" INTEGER NOT NULL,
    "creds" JSONB NOT NULL,
    "info" JSONB NOT NULL,

    CONSTRAINT "GAuth_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "GAuth_user_id_key" ON "GAuth"("user_id");
