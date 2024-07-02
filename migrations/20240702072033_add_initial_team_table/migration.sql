-- CreateTable
CREATE TABLE "InitialTeam" (
    "id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,

    CONSTRAINT "InitialTeam_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "InitialTeam_name_key" ON "InitialTeam"("name");
