-- CreateTable
CREATE TABLE "InitialTeam" (
    "id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "smart_suggestions" TEXT[],

    CONSTRAINT "InitialTeam_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "UserInitialTeam" (
    "id" SERIAL NOT NULL,
    "user_id" INTEGER NOT NULL,
    "initial_team_id" INTEGER NOT NULL,

    CONSTRAINT "UserInitialTeam_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "InitialTeam_name_key" ON "InitialTeam"("name");
